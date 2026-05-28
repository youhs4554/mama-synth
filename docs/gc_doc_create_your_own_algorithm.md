# Crawled Page: Create your own algorithm -
    
        Algorithms -
    
    Grand Challenge
- **Source URL:** [https://grand-challenge.org/documentation/create-your-own-algorithm/](https://grand-challenge.org/documentation/create-your-own-algorithm/)

---

[←

Try out an algorithm](/documentation/try-out-your-algorithm/)

[Create an algorithm page

→](/documentation/create-an-algorithm-page/)

### Create your own algorithm[¶](#create-your-own-algorithm "Permanent link")

If you want to create an Algorithm on Grand Challenge, you will likely recognize yourself in one of the following roles:

* a researcher  who intends to share their algorithm (creating an algorithm outside of a challenge),
* a challenge participant who wants to submit their algorithm,
* a challenge organizer who is looking to create a baseline algorithm, to help participants with submitting their algorithms.

Depending on your role, some steps will differ slightly. In general, you will need to:

1. [Create an algorithm page](/documentation/create-an-algorithm-page/)
2. [Define the Algorithm interface(s)](/documentation/choose-input-and-output-interfaces/)\*
3. [Download example code](/documentation/download-example-code/)
4. [Build and test the container](/documentation/building-and-testing-the-container/)
5. [Deploy your algorithm](/documentation/add-the-algorithm/)
6. [(optional) Upload the model weights separately](/documentation/upload-the-model-weights-separately/)
7. [Try out your algorithm and publish a test case](/documentation/try-out-your-algorithm-and-publish-a-test-case)
8. [Document your algorithm](/documentation/documenting-your-algorithm-for-users/)

If you want (other people) to view results in the CIRRUS viewer, you will probably also want to [Configure how the data is displayed](/documentation/how-to-configure-your-viewer/).

\* If you're a challenge participant, you won't have to define the interfaces, as they will be set by the challenge organizers. However, it is still important to understand [what algorithm interfaces are](/documentation/choose-input-and-output-interfaces/#what-are-algorithm-interfaces).

#### Prerequisites[¶](#prerequisites "Permanent link")

Preparing your algorithm for upload requires Docker.

#### General principle[¶](#general-principle "Permanent link")

On Grand Challenge, we run an algorithm in an isolated piece of software called a [Docker container](https://www.docker.com/resources/what-container/). It packages all the libraries and dependencies that your algorithm needs in order to reliably run on a different machine than yours. Think of the OS, the NVIDIA drivers, Python versions, and the versions of all the libraries and packages necessary for running your algorithm: they are all packaged with a Docker container.

The tutorial takes you through the steps to serve your algorithm in a Docker container that's compatible with the requirements of grand-challenge.org.

On Grand Challenge, you build your algorithm container to process only one set of inputs at a time: this could be a single CT-image, but also an MR image plus a CT image from one patient. Batched inputs are not natively supported, and should be avoided.

As an algorithm developer, you will need to configure at least one interface, describing the required inputs and outputs for your algorithm. This interface lets Grand Challenge know how to read the input(s) and output(s) of your algorithm (more on interfaces later). A user can download the outputs of a job, or they can view the results in the web browser, using our own browser-based viewer (CIRRUS).

Reference the  [runtime-environment information](/documentation/runtime-environment/) for restrictions that apply.

#### Installing Docker: is it necessary?[¶](#installing-docker-is-it-necessary "Permanent link")

Yes, realistically speaking, you will need Docker installed locally. Docker will be needed to build and test containers and save container images. When you are building your first container, you will want to test run it several times while you are inserting your own code. Doing this locally will save you a lot of time and will also give you a better understanding of how containers and container images work and are created.

When you have a stable codebase, you can let the platform create and save container images for you. This works by linking your GitHub repository to your algorithm on Grand Challenge. Note that from the above three steps—build, test, save—this is only the last step. Although you could circumvent installing Docker in this way, extensive debugging will not be possible, because you can now only test after saving an image. Creating your container image in the cloud may take an hour or so, thus the feedback loop is going to be very slow.

Through the feedback that the GC support team received, we found that many users got stuck installing Docker. With its many products and features, Docker can be very overwhelming. As a first time user, you will probably want to install Docker Desktop and run their [hello world](https://hub.docker.com/_/hello-world/#example-output) example to check if everything is working correctly (command: `docker run hello-world`). If you want to learn more, visit [docker.com/get-started/](https://www.docker.com/get-started/).

##### Installing Docker on windows[¶](#installing-docker-on-windows "Permanent link")

When you install Docker, you will need to do so on a unix-based operating system, or on Windows with Windows subsystem for Linux (WSL 2), which is a Linux environment on Windows. If you are using Windows 11 (or newer versions of 10), make sure to follow our [guide for setting up Docker on Windows](/documentation/setting-up-wsl-with-gpu-support-for-windows-11/).

[←

Try out an algorithm](/documentation/try-out-your-algorithm/)

[Create an algorithm page

→](/documentation/create-an-algorithm-page/)