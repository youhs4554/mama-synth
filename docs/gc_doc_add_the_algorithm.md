# Crawled Page: Deploy your algorithm -
    
        Create your own algorithm -
    
    Grand Challenge
- **Source URL:** [https://grand-challenge.org/documentation/add-the-algorithm/](https://grand-challenge.org/documentation/add-the-algorithm/)

---

[←

Build and test the container](/documentation/building-and-testing-the-container/)

[Option 1: Linking a GitHub repository

→](/documentation/linking-a-github-repository-to-your-algorithm/)

### Deploy your algorithm[¶](#deploy-your-algorithm "Permanent link")

We provide two options for deploying algorithms:

1. Push code to a (private) Github repo, and let Grand Challenge build a container image in the cloud.
2. Locally build and export container images with Docker. Then upload a container image directly to Grand Challenge.

The first option is considered best practice because it allows versioning: if your algorithm is linked to a repository, each time you  tag a release, a new container image is built. This makes it easy to revert a faulty update and keeps your code maintainable long after you've moved on in your career.

However, you will generally start with option 2 to test and debug your container locally, before you upload it to Grand Challenge (or before tagging your Github repo in its first release).

Instructions for each option can be found in:

* [Option 1: Link a GitHub repository](/documentation/linking-a-github-repository-to-your-algorithm/)
* [Option 2: Uploading the container image](/documentation/exporting-the-container/)

In both cases, you have the flexibility to include your model weights within the container or [upload the model weights separately](/documentation/upload-the-model-weights-separately/).

[←

Build and test the container](/documentation/building-and-testing-the-container/)

[Option 1: Linking a GitHub repository

→](/documentation/linking-a-github-repository-to-your-algorithm/)