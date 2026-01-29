# py_parallelizer
* Automated testing on PR using github actions
* Semantic release using github actions
* Automatic code coverage report in README

*Notes*  
Workflows trigger when a branch is merged into main!  
To install, please follow all the instructions in this readme.  
The workflows require a PAT set as secret (see further down for instructions)  
See the notes on how to create semantic releases at the bottom of the README.     
  
If you followed all the steps, whenever a PR is merged into `main`, the workflows are triggered and should:
* Ensure that tests pass (before merge)
* Create a code coveraeg report and commit that to the bottom of the README
* Create a semantic release (if you follow the semantic release pattern) and automatically update the version number of your code.


# Install
Cookiecutter template:
* Cd to your new libary location
  * `cd /your/new/library/path/`
* Install cookiecutter using pip
  * `pip install cookiecutter`
* Run the cookiecutter template from this github repo
  * `cookiecutter https://github.com/jonathanvanleeuwen/lib_template`
* Fill in your new library values
* Create new virtual environment
  *  `python -m venv .venv_repo_name`
* Install libary
  *  `pip install -e .`
* Check proper install by running tests
  * `pytest`

## Turn the new local cookiecutter code into a git repo

Open git bash 
```bash
cd C:/your/code/directory
```
To init the repository, add all files and commit
```bash
git init
git add *
git add .github
git add .gitignore
git commit -m "fix: Inital commit"
```

To add the new git repository to your github, -
*  Go to [github](https://github.com/).
-  Log in to your account.
-  Click the [new repository](https://github.com/new) button in the top-right. You’ll have an option there to initialize the repository with a README file, but don’t. Leave the repo empty
- Give the new repo the same name you gave your repo with the cookiecutter
-  Click the “Create repository” button.

Now we want to make sure we are using `main` as main branch name and push the code to github
```bash
git remote add origin https://github.com/username/new_repo_name.git
git branch -M main
git push -u origin main
```

# Protect your main branch
To ensure that only accepted code is put on main, make sure that all changes to main happen using a PR and at least 1
reviewer.
You also want to ensure that no tests are allowed to fail when merging

## Branch Protection
### Ensure branch protection for PRs
In the repo on github go to:
* Settings -> Branches and click "add rule"
* Enable:
  * Require a pull request before merging
    * Require approvals (set the number of required reviewers)
  * Require status checks to pass before merging
    * Require branches to be up to date before merging
  * Require conversation resolution before merging

### Ensure workflow protection
this is not entirely fool proof and secure, but better than nothing, in the repo on github go to:
* Settings -> Actions -> General
* Enable:
  * Allow [owner], and select non-[owner], actions and reusable workflows
* In "Allow specified actions and reusable workflows" add the following string:
  * actions/checkout@v2,
actions/setup-python@v3,
relekang/python-semantic-release@master,
MishaKav/pytest-coverage-comment@main,
actions-js/push@master,

## Create a semantic release PAT and Secrets for the workflow actions
For the semantic release to be able to push new version to the protected branch you need to
create a PAT with the proper permissions and save the pat as a secret in the repo.

### Create PAT
* Click Top right image -> settings
* Developer settings
* Personal access tokens -> Tokens (classic)
* Generate new token -> generate new token (classic)

Settings:
* Note: Semantic release
* Enable:
  * Repo (and all the repo options)
  * workflow
  * admin:repo_hook
* Generate token

Now copy the token (you need this in the next step)

### Create secret
Go to your repo, then:
* Settings -> Secrets -> Actions
* New repository secret
  * Name: SEM_RELEASE
  * Secret: [Your copied PAT token]

The name needs to be the same, as this is wat is used in ".github\workflows\semantic-release.yml"


# Semantic release
https://python-semantic-release.readthedocs.io/en/latest/

The workflows are triggered when you merge into main!!

When committing use the following format for your commit message:
* patch:
  `fix: commit message`
* minor:
  `feat: commit message`
* major/breaking (add the breaking change on the third  line of the message):
    ```
    feat: commit message

    BREAKING CHANGE: commit message
    ```

# Coverage report
<!-- Pytest Coverage Comment:Begin -->
<a href="https://github.com/jonathanvanleeuwen/py_parallelizer/blob/main/README.md"><img alt="Coverage" src="https://img.shields.io/badge/Coverage-86%25-green.svg" /></a><details><summary>Coverage Report </summary><table><tr><th>File</th><th>Stmts</th><th>Miss</th><th>Cover</th><th>Missing</th></tr><tbody><tr><td colspan="5"><b>src/py_parallelizer</b></td></tr><tr><td>&nbsp; &nbsp;<a href="https://github.com/jonathanvanleeuwen/py_parallelizer/blob/main/src/py_parallelizer/basic_function.py">basic_function.py</a></td><td>6</td><td>1</td><td>83%</td><td><a href="https://github.com/jonathanvanleeuwen/py_parallelizer/blob/main/src/py_parallelizer/basic_function.py#L10">10</a></td></tr><tr><td><b>TOTAL</b></td><td><b>7</b></td><td><b>1</b></td><td><b>86%</b></td><td>&nbsp;</td></tr></tbody></table></details>
<!-- Pytest Coverage Comment:End -->
