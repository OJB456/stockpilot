GitHub Repository: Not configured yet (this workspace has no Git remote)

# StockPilot — E-Commerce Inventory Management System

**Live Application:** Not deployed yet<br>
**GitHub Actions:** No remote Actions run is available yet<br>
**Commit Count:** 10 after this documentation milestone (verify with `git rev-list --count main`)

> This report records only results verified in the current workspace. Replace the pending entries with links and evidence after GitHub and Render are configured. Do not present the screenshot placeholders as evidence.

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

The checked-in workflow is `.github/workflows/ci-cd.yml`. Its configured dependency chain is `lint-test` → `build` → `deploy`. The deploy job is limited to a push to `main`; pull requests cannot deploy. The build job starts the image and checks `/health` and the commit SHA. A successful remote Actions run has not yet been verified because no Git remote is configured.

**Screenshot placeholder — workflow file and a real green Actions run:**<br>
`[ADD REAL GITHUB SCREENSHOTS AFTER PUSHING THE REPOSITORY]`

## 8. Testing

Verified locally with Python 3.11.6: Flake8 completed successfully, and pytest reported **28 passed** using temporary SQLite databases. These are local results, not GitHub Actions results. Docker build and container smoke-test results are pending because the Docker daemon did not respond during this audit.

**Screenshot placeholder — local lint and test output:**<br>
`[ADD A REAL TERMINAL SCREENSHOT]`

## 9. Failure Demonstration

A real red GitHub Actions run has not yet been created or verified. The reproducible steps are documented in [docs/failure-demo.md](failure-demo.md). After publishing the repository, change the documented sale assertion on a demo branch, open a pull request, and capture the actual failed `lint-test` job with the dependent `build` and `deploy` jobs skipped. Then restore the assertion, capture the passing pull-request run and merge only after checks pass.

**Screenshot placeholder — real red run and skipped jobs:**<br>
`[ADD AFTER THE FAILURE EXERCISE HAS RUN ON GITHUB]`

## 10. Deployment

`render.yaml` describes a Docker web service on `main`, with automatic deploys disabled and `/health` configured as the health check. No Render service or live URL has been verified yet. Deployment requires a public GitHub repository, a Render service, and the `RENDER_DEPLOY_HOOK` GitHub Actions secret.

**Live Application URL:** Not available yet<br>
**Screenshot placeholder — real Render deployment and live page:**<br>
`[ADD AFTER A DEPLOYMENT COMPLETES AND THE LIVE PAGE IS CHECKED]`

## 11. Commit SHA Verification

The application returns `GIT_COMMIT`, then `RENDER_GIT_COMMIT`, and falls back to `local-dev`. The Docker smoke-test workflow supplies the current GitHub SHA. No deployed SHA has been verified yet.

**GitHub merge commit SHA:** Not available yet<br>
**Live `/health` commit SHA:** Not available yet<br>
**Screenshot placeholder — live health response matched to the merge commit:**<br>
`[ADD AFTER BOTH SHAS HAVE BEEN CHECKED]`

## 12. Challenges

The development requirements named `httpx2`, while FastAPI's test client requires `httpx`. The requirement was corrected to `httpx>=0.27,<1.0`; dependency installation then completed and all 28 local tests passed. The Docker client is present, but the daemon did not answer during this audit, so container verification remains pending.

## Conclusion

The application and local test suite are in place, and local lint and tests pass. The public repository, real red and green Actions runs, Docker smoke test, Render deployment and deployed SHA check still need external setup and verification before this report can be submitted as complete.

## Evidence Checklist

- [ ] Public GitHub repository URL
- [ ] Eight or more meaningful commits
- [ ] Dashboard, Add Product, sell, restock and low-stock screenshots
- [ ] Transaction history screenshot
- [ ] Workflow YAML screenshot
- [ ] Real green and red Actions runs
- [ ] Build and deploy shown skipped after the test failure
- [ ] Fixed green pull-request run and merge
- [ ] Render deployment and live application URL
- [ ] Live `/health` response and matching deployed SHA
- [ ] GitHub Actions URL and verified commit count
