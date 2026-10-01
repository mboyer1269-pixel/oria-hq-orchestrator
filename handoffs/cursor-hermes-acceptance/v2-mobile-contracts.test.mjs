#!/usr/bin/env node
// Reusable checks for the existing HQ contracts named by UI-MODELES-V2.md.
// No UI, no network, no new dependency. HQ_PRODUCT_ROOT defaults to /tmp/hq-hermes.

import assert from "node:assert/strict";
import path from "node:path";
import test from "node:test";
import { pathToFileURL } from "node:url";

const root = process.env.HQ_PRODUCT_ROOT ?? "/tmp/hq-hermes";
const { createJiti } = await import(pathToFileURL(path.join(root, "node_modules/jiti/lib/jiti.mjs")).href);
const jiti = createJiti(import.meta.url, {
  alias: {
    "@": path.join(root, "src"),
    "server-only": path.join(root, "src/scripts/smoke/server-only-stub.mjs"),
  },
});
const source = (relative) => path.join(root, relative);
const { chooseModel } = await jiti.import(source("src/server/ai/model-router.ts"));
const { decideLadder } = await jiti.import(source("src/server/ai/cost-ladder.ts"));
const { executionTargetForModel } = await jiti.import(source("src/server/ai/execution-models.ts"));
const { generateStructuredJson } = await jiti.import(source("src/server/ai/llm-json-provider.ts"));
const { createDevelopmentService } = await jiti.import(source("src/server/missions/development-mission.ts"));

let networkCalls = 0;
globalThis.fetch = () => {
  networkCalls += 1;
  throw new Error("network_forbidden");
};
delete process.env.ANTHROPIC_API_KEY;
delete process.env.OPENAI_API_KEY;
delete process.env.OPENROUTER_API_KEY;
delete process.env.HQ_CALL_RESERVATION;

const prompt = { providerPreference: "auto", systemPrompt: "sys", userPrompt: "bonjour", workspaceId: "synthetic-workspace" };

test("the requested model is not reported as executed", async () => {
  const decision = chooseModel({ message: "bonjour", workspaceId: "synthetic-workspace" });
  assert.equal(decision.executedModelId, null);
  assert.equal(decision.accountingEffect, "none");
  assert.equal(decision.estimate.monetaryUsd, null);
  assert.ok(decision.chosenModelId);
  assert.notEqual(decision.chosenModelId, decision.executedModelId);
});

test("an incompatible model is refused before any provider call", async () => {
  for (const modelId of ["openrouter/free", "google/gemma-4-31b-it:free"]) {
    assert.equal(executionTargetForModel(modelId).callable, false);
    const result = await generateStructuredJson({ ...prompt, modelId });
    assert.equal(result.ok, false);
    assert.equal(result.errorCode, "model_unsupported");
    assert.equal(result.chosenModelId, modelId);
    assert.equal(result.executedModelId, null);
    assert.equal(result.cost.networkRequestSent, false);
    assert.equal(result.attempts.length, 0);
  }
});

test("auto does not call a second paid provider without explicit workspace consent", async () => {
  const calls = { anthropic: 0, openai: 0 };
  const fetchFns = {
    anthropic: async () => { calls.anthropic += 1; throw new Error("network_forbidden"); },
    openai: async () => { calls.openai += 1; throw new Error("network_forbidden"); },
  };
  const denied = await generateStructuredJson({ ...prompt, fetchFns });
  assert.equal(denied.ok, false);
  assert.deepEqual(denied.attempts.map((attempt) => attempt.provider), ["anthropic"]);
  assert.equal(denied.cost.networkRequestSent, false);
  assert.equal(calls.openai, 0);
  const wrongWorkspace = await generateStructuredJson({
    ...prompt,
    fetchFns,
    paidFallback: { authorized: true, workspaceId: "other-workspace" },
  });
  assert.deepEqual(wrongWorkspace.attempts.map((attempt) => attempt.provider), ["anthropic"]);
  const allowed = await generateStructuredJson({
    ...prompt,
    fetchFns,
    paidFallback: { authorized: true, workspaceId: "synthetic-workspace" },
  });
  assert.deepEqual(allowed.attempts.map((attempt) => attempt.provider), ["anthropic", "openai"]);
  assert.equal(calls.anthropic, 0);
  assert.equal(calls.openai, 0);
  assert.equal(allowed.cost.networkRequestSent, false);
});

test("local ladder spend is not a provider quota", () => {
  const unknown = decideLadder({ taskClass: "draft", baseRung: "economy", freeCatalog: [], currentSpend: 0 });
  assert.equal(Object.hasOwn(unknown, "quota"), false);
  assert.equal(unknown.estimatedCost === 0 || unknown.estimatedCost === 1 || unknown.estimatedCost === 5, true);
  assert.equal(unknown.rung, "economy");
  assert.match(unknown.reason, /aucun modèle free éligible/);
});

test("a lost create retried after reconnection keeps one mission", async () => {
  const rows = new Map();
  let loseNext = true;
  const store = {
    save: async (mission) => {
      if (!rows.has(mission.id)) rows.set(mission.id, structuredClone(mission));
      if (loseNext) { loseNext = false; throw new Error("synthetic reconnect"); }
      return structuredClone(rows.get(mission.id));
    },
    load: async (workspaceId, missionId) => {
      const mission = rows.get(missionId);
      return mission?.workspaceId === workspaceId ? structuredClone(mission) : null;
    },
  };
  const service = createDevelopmentService({ enabled: () => true, store: () => store });
  const input = {
    requestId: "32345678-1234-4234-8234-123456789abc",
    title: "Synthetic",
    objective: "Keep one mission",
    scope: "One row",
    acceptanceCriteria: "Same id",
  };
  const context = { workspaceId: "synthetic-workspace", modeId: "hq", actorId: "synthetic-session-owner" };
  assert.equal((await service.create(input, context)).status, "outcome_unknown");
  const recovered = await service.lookup(input.requestId, context.workspaceId);
  assert.equal(recovered.status, "saved");
  assert.equal(recovered.executionRequested, false);
  const retry = await service.create(input, context);
  assert.equal(retry.status, "saved");
  assert.equal(retry.missionId, recovered.missionId);
  assert.equal(rows.size, 1);
});

test("this process did not open a provider socket", () => {
  assert.equal(networkCalls, 0);
});
