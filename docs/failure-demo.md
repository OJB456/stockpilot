# Real GitHub Actions Failure Demonstration

This failure exercise has been completed on the public repository. The verified run record is below. The remaining numbered steps document how to reproduce the demonstration if needed; they are not unverified results.

## Verified Run Record

- Pull request: [#2](https://github.com/OJB456/stockpilot/pull/2)
- Broken-test commit: `3f3ceb96607ac33fe365d9a177cd47bec0cf8257`
- Real red Actions run: [36375525051](https://github.com/OJB456/stockpilot/actions/runs/36375525051)
- Failure: the sale test expected quantity 8, while the application correctly returned 7. `lint-test` failed; dependent `build` and `deploy` jobs were skipped.
- Fix commit: `9d996794c88851e40f88991f0f3851b45e67bf76`
- Real fixed green PR run: [36375640953](https://github.com/OJB456/stockpilot/actions/runs/36375640953). Lint, all 28 tests, Docker build and `/health` SHA smoke test passed; deploy was skipped because the run was a pull request.
- Merge commit: `4fe56160235f594469751dfa7a6be25a33479bad`
- Post-merge main run: [36375726078](https://github.com/OJB456/stockpilot/actions/runs/36375726078). Lint/test and build passed; deploy failed because `RENDER_DEPLOY_HOOK` was not configured. A Render service and live URL remain pending.

## Reproduce the Demo: Prerequisites

- Push StockPilot to a public GitHub repository.
- Confirm `.github/workflows/ci-cd.yml` is visible on `main`.
- Configure the Render service and `RENDER_DEPLOY_HOOK` secret if deployment evidence is expected.
- Confirm the normal workflow succeeds before changing a test.

## Create a Failing Pull Request

1. In PowerShell, fetch the latest main and create the branch:

   ```powershell
   git switch main
   git pull origin main
   git switch -c demo/fail-pipeline
   ```

2. Open `tests/test_main.py` and find `test_sale_reduces_stock_and_records_sale_transaction`. Change only `assert product.quantity == 7` to `assert product.quantity == 8`. This is intentionally wrong: starting with 10 and selling 3 leaves 7.
3. Commit using this exact message:

   ```text
   demo: intentionally break a test to prove pipeline blocks bad deploys
   ```

4. Push the branch:

   ```powershell
   git push -u origin demo/fail-pipeline
   ```

5. On GitHub, open a pull request from `demo/fail-pipeline` to `main`.
6. Wait for the real Actions run. Expected result: `lint-test` fails, `build` is skipped, and `deploy` is skipped. Open the run and capture a screenshot that shows the failed test and skipped dependent jobs.

## Fix and Merge

7. Change the assertion back to `assert product.quantity == 7`.
8. Commit using this exact message:

   ```text
   fix: revert intentional test break
   ```

9. Push the branch again:

   ```powershell
   git push
   ```

10. Wait for the new PR run. Expected result: `lint-test` and `build` pass; `deploy` is skipped because the event is still a pull request. Capture the green run and the skipped deploy job.
11. Merge the pull request to `main`. The push event on `main` runs the workflow again. The recorded main run passed lint, Docker build and smoke test but could not deploy until the Render service and GitHub secret are configured.
12. After Render is configured, verify the completed service deployment and live application. Compare the commit shown in `/health` and the footer with the deployed merge commit before reporting deployment as successful.

## Evidence to Save

- [The failed Actions run](https://github.com/OJB456/stockpilot/actions/runs/36375525051) with the actual assertion failure.
- The run graph showing `build` and `deploy` skipped.
- [The fixed PR run](https://github.com/OJB456/stockpilot/actions/runs/36375640953) showing successful lint/test and build, and skipped deploy.
- A successful `main` run and Render deployment (still pending the Render service and secret).
- The live dashboard and `/health` response showing the merge commit SHA.

Use screenshots from your own GitHub and Render accounts. Do not create or edit screenshots to imply a run or deployment that did not happen. A Deploy Hook request being accepted starts a Render deploy; confirm the deploy is complete in Render and verify the live health response before reporting deployment as successful.
