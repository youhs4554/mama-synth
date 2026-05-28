# Crawled Page: Setting up Docker on Windows -
    
        Create your own algorithm -
    
    Grand Challenge
- **Source URL:** [https://grand-challenge.org/documentation/setting-up-wsl-with-gpu-support-for-windows-11/](https://grand-challenge.org/documentation/setting-up-wsl-with-gpu-support-for-windows-11/)

---

[←

Document your algorithm](/documentation/documenting-your-algorithm-for-users/)

[Runtime Environment

→](/documentation/runtime-environment/)

### Setting up Docker on Windows[¶](#setting-up-docker-on-windows "Permanent link")

In this tutorial we will show you how to set up Docker (with GPU support) on Windows. This tutorial assumes that you do not yet have [Windows Subsystem for Linux (WSL 2)](https://learn.microsoft.com/en-us/windows/wsl/) or [Docker](https://www.docker.com/) installed.

If you do not need GPU support, you can skip the steps involving Nvidia software.

#### 1. Install the Nvidia driver[¶](#1-install-the-nvidia-driver "Permanent link")

The required driver depends on your GPU. You can install the driver for your specific GPU [here](https://www.nvidia.com/Download/index.aspx?lang=en-us).

#### 2. Install Windows subsystem for Linux[¶](#2-install-windows-subsystem-for-linux "Permanent link")

Find the instructions on how to [install Windows subsystem for Linux here](https://learn.microsoft.com/en-us/windows/wsl/install).

Open the command window and execute the lines below, this will install WSL with Ubuntu. Although we are using Ubuntu in this tutorial, any flavor of Linux can be installed in this step.

```
wsl.exe --install -d Ubuntu
wsl.exe --update
```

After installation, make sure to run the commands from the following steps through the Ubuntu terminal.

#### 3. Install Docker Engine[¶](#3-install-docker-engine "Permanent link")

If you have previously installed Docker, make sure to first remove your current version before installing the new version. If this is the first time that you're installing Docker, you can skip this first line.

```
$ sudo apt-get remove docker docker-engine docker.io containerd runc
```

Install Docker Engine, following the instructions for installing on Ubuntu found in the [Docker docs](https://docs.docker.com/engine/install/ubuntu/).

After installation we should verify that Docker has been installed correctly. Let's start Docker and run an example hello world container.

```
$ sudo service docker start
$ docker run hello-world
```

#### 4. Post-installation steps[¶](#4-post-installation-steps "Permanent link")

By default we can now only run Docker commands as root user. In order to run Docker without the sudo prefix we need to perform the following steps. Note that although these steps are recommended, they are not obligatory for running Docker on Linux.

First we create a Docker group.

```
$ sudo groupadd docker
```

Next, we add our username to the group. Make sure to replace $USER by your own username.

```
$ sudo usermod -aG docker $USER
```

Now we have to activate these changes to our group and verify that we can use the Docker command without the sudo prefix.

```
$ newgrp docker
$ docker run hello-world
```

You should now see a message in your terminal that your installation works correctly. If you obtain any errors, make sure to check out the [troubleshooting guide](https://docs.docker.com/engine/install/linux-postinstall/#troubleshooting) in the Docker docs.

#### 5. Install the Nvidia container toolkit[¶](#5-install-the-nvidia-container-toolkit "Permanent link")

This toolkit is required to ensure compatibility between your Nvidia driver and Docker. Run the following commands in your newly installed Ubuntu terminal.

```
$ distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
$ curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add
$ curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list
```

You can now install the toolkit through the following lines.

```
$ sudo apt-get update
$ sudo apt-get install -y nvidia-docker2
```

After installation it may be a good idea to restart your computer to finalize all installations.

#### 6. Test a benchmark Docker container[¶](#6-test-a-benchmark-docker-container "Permanent link")

To verify that the installation has been successful we will run a benchmark test with a Nvidia Docker image that requires a GPU. When this test is successful, you should see that your GPU is displayed in the output.

```
$ sudo service docker start
$ docker run --gpus all nvcr.io/nvidia/k8s/cuda-sample:nbody nbody -gpu -benchmark
```

[←

Document your algorithm](/documentation/documenting-your-algorithm-for-users/)

[Runtime Environment

→](/documentation/runtime-environment/)