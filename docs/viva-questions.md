# StockPilot Viva Preparation

## Explain StockPilot in 60 Seconds

StockPilot is a small inventory management web app for an online shop. It uses FastAPI to handle browser requests, Jinja2 to render pages, SQLAlchemy to work with the database, and SQLite to store products and transactions. Users can add products, sell stock and restock items. Every successful stock change is recorded, and the app prevents a sale from making stock negative. GitHub Actions runs linting, tests and a Docker smoke test. Only a successful push to `main` can trigger the Render deployment. The `/health` endpoint shows which commit is running.

## Explain the CI/CD Pipeline in 60 Seconds

The workflow starts for pushes and pull requests. First, `lint-test` installs the development requirements, runs Flake8 and runs pytest against temporary SQLite databases. The `build` job depends on that job, so it is skipped if lint or tests fail. It builds the production Docker image, starts a container and checks `/health`, including the Git commit SHA. The `deploy` job depends on the build and only runs on a push to `main`. It uses a GitHub Actions secret to call Render's Deploy Hook. Pull requests can be checked but never deployed.

## Explain How the Failed Pipeline Proves Deployment Protection

I change one expected stock quantity in a test so it no longer matches the app's real behavior. GitHub Actions runs the test on my pull request and reports `lint-test` as failed. The Docker `build` job needs `lint-test`, and `deploy` needs `build`, so GitHub marks both later jobs as skipped. I restore the correct assertion, push the fix, and show a passing run. The GitHub Actions run history is the evidence that a failing check stopped the later build and deployment jobs.

## Questions and Short Answers

1. **What is Git?** Git records changes to files so I can compare versions and return to earlier work.
2. **What is GitHub?** GitHub hosts Git repositories online and adds collaboration tools such as pull requests and Actions.
3. **What is a commit?** A commit is a saved snapshot of changes with a message explaining the change.
4. **What is a branch?** A branch is a separate line of work where I can make changes before merging them.
5. **What is a pull request?** A pull request proposes merging a branch and lets the checks run before the change reaches `main`.
6. **What is CI?** Continuous Integration automatically checks changes when they are pushed or proposed.
7. **What is CD in this project?** After checks pass on `main`, the workflow requests a Render deployment.
8. **What is GitHub Actions?** It is GitHub's automation service for running workflows from YAML files in the repository.
9. **What is a workflow?** A workflow defines when automation runs and which jobs it performs.
10. **What is a job?** A job is a group of workflow steps that runs on a runner.
11. **What is a step?** A step runs a command or uses an action inside a job.
12. **What does `needs` do?** It makes a job wait for another job and skip if that dependency fails.
13. **What is the deployment gate?** The `lint-test` → `build` → `deploy` dependencies prevent bad code from reaching deployment.
14. **Why can a pull request not deploy?** The deploy condition only accepts a push event whose ref is `refs/heads/main`.
15. **What is Docker?** Docker packages an application and its dependencies into an image that can run as a container.
16. **What is a Docker image?** An image is the packaged template Docker uses to start a container.
17. **What is a container?** A container is a running instance of an image.
18. **What is a smoke test?** It is a quick end-to-end check that the running app starts and responds to a key request.
19. **What does the StockPilot smoke test check?** It requests `/health` from the container and compares the returned commit with the workflow SHA.
20. **What is Render?** Render is the cloud platform used to run the Docker web service.
21. **What is a Deploy Hook?** It is a secret URL that lets an authorized request start a Render deployment.
22. **Why is the hook a GitHub secret?** The URL can trigger deployment, so it must not be exposed in source code or logs.
23. **What is FastAPI?** FastAPI is the Python web framework that maps HTTP requests to application functions.
24. **What is Jinja2?** Jinja2 fills HTML templates with data from the application.
25. **What is SQLAlchemy?** It maps Python classes to database tables and lets the app query and update them.
26. **Why use SQLite?** It stores this small project's data in one file without a separate database server.
27. **How are tests kept away from the local database?** Each test creates an app configured with a temporary SQLite file.
28. **What does pytest do?** It discovers and runs Python tests and reports which behavior passed or failed.
29. **What does Flake8 do?** It reports common Python style and formatting problems.
30. **What is a REST endpoint?** It is a URL and HTTP method that expose an application operation or resource.
31. **Why use POST for selling stock?** Selling changes stored data, so POST is used rather than a read-only GET request.
32. **What is an environment variable?** It is configuration supplied to a process from outside the source code.
33. **What does `/health` return?** It returns an `ok` status and the best available commit value.
34. **What is a commit SHA?** It is the unique identifier Git assigns to a commit.
35. **How does the app prevent negative stock?** The sale updates the row only when its current quantity is at least the requested amount.
36. **What happens when a sale is too large?** The stock update is rejected, no sale transaction is inserted, and the user sees an error.
37. **What happens after an intentional test failure?** `lint-test` fails, and the dependent build and deploy jobs are skipped.
38. **What is one Render free-plan limitation?** The service can spin down and its local SQLite file can be lost, so it is for demonstrations only.
