import test from "node:test";
import assert from "node:assert/strict";
import { classify } from "../src/email/classify.ts";

test("classifies common support request types", () => {
  assert.equal(classify("How do I update the site logo?"), "how_to");
  assert.equal(classify("Please refund this duplicate payment"), "refund_cancellation");
  assert.equal(classify("Our checkout page shows an error"), "troubleshooting");
});
