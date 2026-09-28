# Real GitHub Actions Failure Demonstration

This exercise creates one real test failure on GitHub. Do it only after the repository is public, the workflow is present on `main`, and the workflow has at least one successful run. Keep the intentionally failing assertion to one line.

## Before the Demo

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
11. Merge the pull request to `main`. The push event on `main` runs the workflow again. After lint, Docker build and smoke test succeed, the deploy job sends the exact pushed SHA to Render.
12. Open the GitHub merge commit, the Render service's successful deploy, and the live application. Compare the commit shown in `/health` and the footer with the deployed merge commit.

## Evidence to Save

- The failed Actions run with the actual assertion failure.
- The run graph showing `build` and `deploy` skipped.
- The fixed PR run showing successful lint/test and build, and skipped deploy.
- The successful `main` run and Render deployment.
- The live dashboard and `/health` response showing the merge commit SHA.

Use screenshots from your own GitHub and Render accounts. Do not create or edit screenshots to imply a run or deployment that did not happen. A Deploy Hook request being accepted starts a Render deploy; confirm the deploy is complete in Render and verify the live health response before reporting deployment as successful.
