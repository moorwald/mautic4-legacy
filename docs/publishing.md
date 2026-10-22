# GitHub source and GHCR release process

## Destination and authorization
Sven authorized the public moorwald GitHub repository and a repository-driven image publication path on 22 October 2026:
- Source: https://github.com/moorwald/mautic4-legacy
- First-release image tags:
  - ghcr.io/moorwald/mautic4-legacy:4.4.13-php74-r1-apache
  - ghcr.io/moorwald/mautic4-legacy:4.4.13-php74-r1-fpm

This approval does not authorize changes to running installations, new Mautic features or dependency modernization. The first pair was uploaded by manual workflow 39785595624 with its public source Release; Sven completed public visibility, and both anonymous manifest requests, Docker pulls and exact runtime revision checks passed on 22 October 2026 as recorded in status.md.

## What ordinary pushes do
Pushes to main and pull requests run a read-only verification job: build both amd64 images, test isolated fresh/existing installations, report inherited advisories and verify the byte-identical upstream payload. Evidence artifacts exclude passwords, raw SQL, customer data, downloaded archives and general logs.

These jobs have no package-write permission and do not log in to GHCR. No automatic publication occurs on push or tags.

## Before the first image release
The canonical machine-readable checklist is [release-readiness.json](release-readiness.json). The first-release items have reviewed local evidence in [status](status.md); final CI must repeat the technical checks and source collection:
- Scoped image/runtime delta review, not a full Mautic application audit.
- Bounded isolated SMTP smoke verification.
- Corresponding-source/license handoff and exact-source references/availability for redistributed components.

Known inherited Mautic/library findings do not have to disappear. They remain disclosed according to [the scoped assessment](security-assessment.md).

The checklist is an explicit human-reviewed assertion, not an automatic claim or a substitute for tests. The publish job fails while any required assertion is false. Do not flip fields merely to get a green run.

## Manual release
1. Commit the reviewed final source/checklist to main. Confirm ordinary verification passes on that exact commit.
2. Open Actions → Verify images and manually publish → Run workflow, choose main and set publish=true.
3. The publish job first checks readiness, then repeats the full image verification on the selected commit.
4. Collect exact corresponding source files, verify signed indexes/checksums, preserve licence texts and create the handoff bundle from the actual built images. The manual job then uses the repository-scoped ephemeral GITHUB_TOKEN with packages:write for GHCR and contents:write for the GitHub source Release. Automatic verification remains read-only. No personal registry token or repository-stored credentials are needed.
5. The publication script verifies source-revision labels and pushes the EXACT locally tested image IDs, not a newly rebuilt substitute. Existing r1 tags must not be overwritten; a later revised build needs a deliberate new revision.
6. The handoff is attached to a draft GitHub Release before pushing, then both remote manifests are attached and the Release is published. Inspect BOTH remote manifests. A partial push is possible if the second upload fails: stop, record it and reconcile explicitly rather than claiming the pair was atomically released.
7. Complete the public visibility and anonymous-pull checks below before announcing availability.

GitHub Actions/organization policies can restrict package creation. Do not bypass those policies with SSH or a personal token found elsewhere.

## GHCR visibility is separate from repository visibility
GitHub's Container Registry initially creates packages as private, even when they inherit access permissions from a public source repository. The image source label links the package to this repo BEFORE publication, but does not itself make the package public.

If Public is disabled by organization administrators, an organization owner must first allow **Public** under **Organization Settings → Packages → Package Creation**: https://github.com/organizations/moorwald/settings/packages. This permits public packages; it does not automatically publish existing private packages.

After the first push, an authorized package/org administrator must open https://github.com/orgs/moorwald/packages/container/mautic4-legacy/settings and set visibility to Public. The available REST/GraphQL APIs do not offer this visibility change, and the isolated agent browser is not authenticated; Sven may need to perform this one UI step. GitHub documents this as an irreversible visibility change. Then test anonymous manifest access and pulls from a context with no registry credentials, and independently confirm both PHP package revisions. Do not announce a public image based only on authenticated pulls.

The r1 pair completed this sequence on 22 October 2026. Public verification evidence and immutable manifest digests are in [status](status.md) and the release attachment public-availability.json. Neither image was rebuilt or retagged during this post-publication verification.

Source: https://docs.github.com/en/packages/learn-github-packages/configuring-a-packages-access-control-and-visibility

## Public announcement
State the two addressed PHP CVEs, amd64-only scope, explicit unsupported/unofficial status, unchanged application payload, preserved older volumes, inherited application/plugin risks, digest-pinned example pulls and backup requirements. Do not call this a supported or comprehensively secure Mautic 4 release.
