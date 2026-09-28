GitHub Repository: https://github.com/OJB456/stockpilot (verified public)

# StockPilot — E-Commerce Inventory Management System

**Live Application:** Not deployed yet<br>
**GitHub Actions:** [Green fixed-PR run](https://github.com/OJB456/stockpilot/actions/runs/36375640953) — lint/test and Docker smoke test passed, deploy skipped; [red failure-demo run](https://github.com/OJB456/stockpilot/actions/runs/36375525051)<br>
**Commit Count:** 18 on `main` after these documentation updates (verified with `git rev-list --count main`)

> This report records only verified results. Render deployment and live-site fields remain pending. Screenshot placeholders are not evidence.

## 1. Problem Statement

Small e-commerce sellers need a current view of product quantities and a reliable record of stock changes. Manual tracking can become outdated after sales or restocks. StockPilot provides a browser-based inventory view, records successful stock changes, and prevents a sale from reducing stock below zero.

## 2. Objective

- Build a small inventory application that can run locally and in a Docker container.
- Store products and stock transactions through SQLAlchemy and SQLite.
- Validate form input and keep stock quantities consistent.
- Use GitHub Actions to gate the image smoke test and deployment.
- Make the deployed commit visible through the health endpoint and page footer.

## 3. Features

- Dashboard totals for products, stock units, inventory value and low-stock products.
- Product creation with normalized, unique SKUs.
- Sale and restock forms with positive quantity validation.
- Transaction history for successful sales and restocks.
- Separate in-stock, low-stock and out-of-stock statuses.
- `GET /health` returning an `ok` status and the available commit value.

## 4. Technology Stack

Python 3.11, FastAPI, Jinja2, SQLAlchemy, SQLite, pytest, Flake8, Docker, GitHub Actions and Render.

## 5. Architecture

The browser sends requests to FastAPI. Route handlers validate form data and use SQLAlchemy sessions to read or update SQLite. Jinja2 renders the dashboard, product form and transaction history. Docker packages the service. GitHub Actions is configured to lint, test, build and smoke-test before its main-branch deploy job can request a Render deployment.

**Screenshot placeholder — dashboard with browser address bar:**<br>
`[ADD A REAL SCREENSHOT AFTER THE APPLICATION IS RUNNING]`

## 6. Database

The `products` table stores a product name, unique SKU, non-negative quantity, unit price, low-stock threshold and creation time. The `transactions` table stores a product reference, sale or restock type, positive quantity and timestamp. A product can have multiple transactions. Stock updates and their transaction records are committed together.

## 7. CI/CD Pipeline

The checked-in workflow is `.github/workflows/ci-cd.yml`. Its dependency chain is `lint-test` → `build` → `deploy`. Deploy runs only for a push to `main`; pull requests cannot deploy. The build starts the image and checks `/health` and the commit SHA. The real red run [36375525051](https://github.com/OJB456/stockpilot/actions/runs/36375525051) failed the deliberately incorrect sale assertion (actual quantity 7, expected 8), and both dependent jobs were skipped. The fixed PR run [36375640953](https://github.com/OJB456/stockpilot/actions/runs/36375640953) passed lint/test and build, with deploy skipped. After the fix was merged in PR #2, main run [36375726078](https://github.com/OJB456/stockpilot/actions/runs/36375726078) passed lint/test and build but failed at deploy because `RENDER_DEPLOY_HOOK` was not configured.

**Screenshot placeholder — workflow file and a real green Actions run:**<br>
`[ADD REAL GITHUB SCREENSHOTS AFTER PUSHING THE REPOSITORY]`

## 8. Testing

Verified locally with Python 3.11.6: Flake8 completed successfully, and pytest reported **28 passed** using temporary SQLite databases. The first GitHub Actions run also passed its Flake8, pytest, Docker build, container startup and `/health` SHA smoke test. Its only failed job was deploy because the Render secret is not configured yet.

**Screenshot placeholder — local lint and test output:**<br>
`[ADD A REAL TERMINAL SCREENSHOT]`

## 9. Failure Demonstration

A real red GitHub Actions run is verified on [PR #2](https://github.com/OJB456/stockpilot/pull/2). Run [36375525051](https://github.com/OJB456/stockpilot/actions/runs/36375525051) failed the sale test and marked `build` and `deploy` skipped. The failed commit was `3f3ceb96607ac33fe365d9a177cd47bec0cf8257`. Fix commit `9d996794c88851e40f88991f0f3851b45e67bf76` restored the correct assertion; run [36375640953](https://github.com/OJB456/stockpilot/actions/runs/36375640953) passed lint/test and Docker smoke test, with deploy skipped because it was a PR. PR #2 was merged as `4fe56160235f594469751dfa7a6be25a33479bad`. The steps and evidence URLs are recorded in [docs/failure-demo.md](failure-demo.md).

**Screenshot placeholder — real red run and skipped jobs:**<br>
`[ADD AFTER THE FAILURE EXERCISE HAS RUN ON GITHUB]`

## 10. Deployment

`render.yaml` describes a Docker web service on `main`, with automatic deploys disabled and `/health` configured as the health check. Post-merge main run [36375726078](https://github.com/OJB456/stockpilot/actions/runs/36375726078) passed lint/test and Docker build/smoke test but failed at deploy because no Render service or `RENDER_DEPLOY_HOOK` secret has been configured. No live URL is available yet.

**Live Application URL:** Not available yet<br>
**Screenshot placeholder — real Render deployment and live page:**<br>
`[ADD AFTER A DEPLOYMENT COMPLETES AND THE LIVE PAGE IS CHECKED]`

## 11. Commit SHA Verification

The application returns `GIT_COMMIT`, then `RENDER_GIT_COMMIT`, and falls back to `local-dev`. The Docker smoke-test workflow supplies the current GitHub SHA. No deployed SHA has been verified yet.

**GitHub merge commit SHA:** `4fe56160235f594469751dfa7a6be25a33479bad` (PR #2)<br>
**Live `/health` commit SHA:** Not available yet<br>
**Screenshot placeholder — live health response matched to the merge commit:**<br>
`[ADD AFTER BOTH SHAS HAVE BEEN CHECKED]`

## 12. Challenges

The development requirements named `httpx2`, while FastAPI's test client requires `httpx`. The requirement was corrected to `httpx>=0.27,<1.0`; dependency installation then completed and all 28 local tests passed. The local Docker engine returned an internal error, but GitHub Actions' Linux runner built and smoke-tested the image successfully. The main deploy job correctly failed while the Render secret was absent.

## Conclusion

The public repository, ten initial project milestones, real green and red Actions runs, blocked-build failure gate, fixed PR run and merge are verified. Render service creation, its Deploy Hook secret, a successful main deployment, a live URL and deployed SHA verification remain outstanding.

## Evidence Checklist

- [x] Public GitHub repository URL
- [x] Eight or more meaningful commits
- [ ] Dashboard, Add Product, sell, restock and low-stock screenshots
- [ ] Transaction history screenshot
- [ ] Workflow YAML screenshot
- [x] Real green and red Actions runs
- [x] Build and deploy shown skipped after the test failure
- [x] Fixed green pull-request run and merge
- [ ] Render deployment and live application URL
- [ ] Live `/health` response and matching deployed SHA
- [ ] GitHub Actions URL and verified commit count
