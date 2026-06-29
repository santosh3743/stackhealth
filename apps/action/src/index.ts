// StackHealth GitHub Action — scores the PR head and the base it's
// merging into, posts a sticky comment with both grades and the delta,
// and (optionally) fails the check if the PR grade drops below a
// threshold.
//
// Triggered on `pull_request`. No-op for other events.

import * as core from "@actions/core";
import * as github from "@actions/github";

import { ApiClient, ApiError, gradeAtLeast, poll, type ScanRead } from "./api.js";
import { COMMENT_MARKER, renderComment } from "./comment.js";

const TIMEOUT_SECONDS = 600;

async function run(): Promise<void> {
  const email = core.getInput("email", { required: true });
  const minGrade = core.getInput("min-grade").trim();
  const apiBase = core.getInput("api-base") || "https://api.stackhealth.dev";
  const siteBase = core.getInput("site-base") || "https://stackhealth.dev";
  const token = core.getInput("github-token", { required: true });
  const ciToken = core.getInput("ci-token");
  if (ciToken) core.setSecret(ciToken);

  const ctx = github.context;
  if (ctx.eventName !== "pull_request" && ctx.eventName !== "pull_request_target") {
    core.warning(
      `StackHealth action skipped: event "${ctx.eventName}" is not a pull request.`,
    );
    return;
  }

  const pr = ctx.payload.pull_request as
    | {
        number: number;
        base: { ref: string; repo: { full_name: string } };
        head: { ref: string; repo: { full_name: string } };
      }
    | undefined;
  if (!pr) {
    core.setFailed("Could not read pull_request payload — is the trigger configured?");
    return;
  }

  const baseRepoSlug = pr.base.repo.full_name;
  const headRepoSlug = pr.head.repo.full_name;
  const baseRef = pr.base.ref;
  const headRef = pr.head.ref;

  core.info(`Base: ${baseRepoSlug}@${baseRef}`);
  core.info(`PR:   ${headRepoSlug}@${headRef}`);

  const client = new ApiClient(apiBase, ciToken || undefined);

  let base: ScanRead;
  let head: ScanRead;
  try {
    [base, head] = await Promise.all([
      scoreOne(client, baseRepoSlug, baseRef, email, "base"),
      scoreOne(client, headRepoSlug, headRef, email, "head"),
    ]);
  } catch (e) {
    if (e instanceof ApiError) {
      core.setFailed(`StackHealth API error (${e.status}): ${e.message}`);
    } else {
      core.setFailed(`StackHealth scan failed: ${(e as Error).message}`);
    }
    return;
  }

  const body = renderComment({
    base,
    head,
    baseRepoSlug,
    headRepoSlug,
    baseRef,
    headRef,
    siteBase,
  });

  await upsertComment(token, pr.number, body);

  // Surface outputs so downstream steps can branch on them.
  core.setOutput("base-grade", base.grade ?? "");
  core.setOutput("head-grade", head.grade ?? "");
  core.setOutput("base-score", String(base.overall_score ?? ""));
  core.setOutput("head-score", String(head.overall_score ?? ""));
  core.setOutput(
    "delta",
    String((head.overall_score ?? 0) - (base.overall_score ?? 0)),
  );

  if (minGrade && !gradeAtLeast(head.grade, minGrade)) {
    core.setFailed(
      `PR grade ${head.grade ?? "?"} is below the required minimum ${minGrade}.`,
    );
    return;
  }

  if (head.status === "failed") {
    core.setFailed(`PR scan failed: ${head.failure_reason ?? "unknown reason"}`);
  }
}

async function scoreOne(
  client: ApiClient,
  repoSlug: string,
  ref: string,
  email: string,
  label: "base" | "head",
): Promise<ScanRead> {
  const repoUrl = `https://github.com/${repoSlug}`;
  core.info(`Submitting ${label} scan for ${repoSlug}@${ref}…`);
  const submitted = await client.submit(repoUrl, email, ref);
  core.info(`Polling ${label} scan ${submitted.scan_id}…`);
  return poll(client, submitted.scan_id, TIMEOUT_SECONDS, (s) => {
    core.debug(`${label} scan ${submitted.scan_id}: ${s.status}`);
  });
}

// Find an existing StackHealth comment on this PR (by marker) and edit
// it; otherwise create a new one. Stops the action from spamming the PR
// with one comment per push.
async function upsertComment(token: string, prNumber: number, body: string): Promise<void> {
  const octokit = github.getOctokit(token);
  const { owner, repo } = github.context.repo;

  const existing = await octokit.paginate(octokit.rest.issues.listComments, {
    owner,
    repo,
    issue_number: prNumber,
    per_page: 100,
  });

  const ours = existing.find((c) => c.body?.includes(COMMENT_MARKER));
  if (ours) {
    await octokit.rest.issues.updateComment({
      owner,
      repo,
      comment_id: ours.id,
      body,
    });
    core.info(`Updated comment ${ours.id}`);
  } else {
    const created = await octokit.rest.issues.createComment({
      owner,
      repo,
      issue_number: prNumber,
      body,
    });
    core.info(`Created comment ${created.data.id}`);
  }
}

run().catch((e) => {
  core.setFailed((e as Error).message);
});
