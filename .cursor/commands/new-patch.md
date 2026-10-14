# New patch

The user's message after this command is a patch request.
1. Create the next `P-###` entry in `memory/06_PATCH_QUEUE.md` using the template there. Paste the request **verbatim**.
2. Write your interpretation (scope, affected tasks, affected files). If ambiguous, ask first.
3. Check `memory/05_DECISIONS.md` and `memory/01_MASTER_PLAN.md` for conflicts; if the patch changes the plan, add a decision entry and edit the plan.
4. Implement with the smallest safe change. Add or update tests.
5. Verify (tests / metrics). Record the verification in the patch entry.
6. Close the patch (`DONE`) and run the Session END protocol.
