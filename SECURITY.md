# Security policy

This repository holds a dataset of publicly documented security events and a small
set of scripts that validate it and build a static site. It runs no service and
stores no secrets.

## Reporting a vulnerability in this repository

If you find a problem in the scripts, the workflows or the generated site (for
example a cross-site scripting bug in the HTML builder, or a workflow that could
be abused from a pull request), please do not open a public issue. Use GitHub's
private vulnerability reporting on this repository ("Security" tab, "Report a
vulnerability"), or e-mail the maintainer at the address on the GitHub profile
of @basitalisandhu. You will get an acknowledgement within seven days.

## What not to send here

The dataset records events that are already public. Do not report an
unpublished vulnerability in a third-party product to this repository, and do
not open an issue or pull request that discloses one. Report it to the affected
vendor first; once a public advisory, write-up or article exists, it can be
added as an incident (see CONTRIBUTING.md).

## Supported versions

Only the `main` branch is maintained.
