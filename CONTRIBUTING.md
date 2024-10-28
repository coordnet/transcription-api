# Contributing to Transcription API

## Pre-commit

We use [pre-commit](https://pre-commit.com/) to enforce certain standards before committing. Please visit the page to install and then run in the repository:

```bash
pre-commit install
pre-commit install --hook-type commit-msg
```

Please be aware that if you fail to do so your PR may be not be accepted until it has been ran.

## Commit Message Guidelines

We follow the [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) specification commit messages.

### Type

Must be one of the following:

- **build**: Related to the build process (e.g. pre-commit, npm, pip)
- **ci**: CI configuration (e.g. GitHub Actions)
- **docs**: Documentation
- **feat**: Adding a feature
- **fix**: Fixing a bug
- **perf**: Improvements to performance
- **refactor**: Changes that restructure code but do not change the function
- **test**: Related to tests
