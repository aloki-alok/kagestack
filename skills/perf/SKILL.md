---
name: perf
description: Make something measurably faster, or explain why it is slow. Use for slow pages, slow queries, high latency, timeouts, or a speedup or regression claim.
---

# Perf

Read `${CLAUDE_PLUGIN_ROOT}/principles.md` before step 1.

Every change ties to a measurement. Reading the code is not measuring it.

1. **Write the claim first,** in the words you would ship: "the campaign page loads in 2 s at p50 with 10k contacts".
2. **Measure the baseline** on the real path a user waits on, with realistic data. Run it at least 5 times.
   Done when you have the median, the range, and the error count.
3. **Find the limiter.** Profile in a run you do not report. Name what bounds the number: a query, CPU, I/O, the network, a lock.
   Done when you can answer "why not twice as fast?"
4. **Fix the cheapest way first,** and stop when the target is met:
   don't do the work, don't do it twice, do less, do it later, do it in the background, do it in parallel, do it cheaper.
5. **Measure again,** alternating old and new runs so warmup and caches favor neither.
   Done when the gap is bigger than the run-to-run spread.
6. **Check the number is real.**
   - Did anything error?
   - Was each side set up the way production runs it?
   - Does the gain fit the limits? Removing a step that takes 10% of the run gives at most about 11%.

## Reply

The verdict first (faster, slower, no difference, or inconclusive),
then before and after with the unit, the run count, the range, and the limiter.
