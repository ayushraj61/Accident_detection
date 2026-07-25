import json
import os

notebook = {
  "cells": [
    {
      "cell_type": "markdown",
      "metadata": {},
      "source": [
        "# AI-AIDERS: Colab Training Pipeline\n",
        "This notebook trains your LSTM using a Kaggle Dataset and your local `detection` code."
      ]
    },
    {
      "cell_type": "code",
      "execution_count": None,
      "metadata": {},
      "outputs": [],
      "source": [
        "!pip install ultralytics kaggle opencv-python"
      ]
    },
    {
      "cell_type": "markdown",
      "metadata": {},
      "source": [
        "### 1. Authenticate with Kaggle\n",
        "Your Kaggle credentials have been automatically embedded here so you don't need to upload anything manually!"
      ]
    },
    {
      "cell_type": "code",
      "execution_count": None,
      "metadata": {},
      "outputs": [],
      "source": [
        "!mkdir -p ~/.kaggle\n",
        "!echo '{\"username\":\"ayushraj6137\",\"key\":\"KGAT_d05db72814d249ea0db582d88141d0c3\"}' > ~/.kaggle/kaggle.json\n",
        "!chmod 600 ~/.kaggle/kaggle.json"
      ]
    },
    {
      "cell_type": "markdown",
      "metadata": {},
      "source": [
        "### 2. Download Car Crash Dataset\n",
        "We are using `ckay16/car-crash-dataset` (or another CCTV dataset). This takes a few minutes."
      ]
    },
    {
      "cell_type": "code",
      "execution_count": None,
      "metadata": {},
      "outputs": [],
      "source": [
        "!kaggle datasets download -d ckay16/car-crash-dataset-cctv-and-dashcam\n",
        "# Note: If Kaggle says the dataset name changed, search Kaggle for 'car crash cctv' and replace the ID above.\n",
        "!unzip -q car-crash-dataset-cctv-and-dashcam.zip -d dataset\n",
        "!ls dataset/"
      ]
    },
    {
      "cell_type": "markdown",
      "metadata": {},
      "source": [
        "### 3. Upload your `detection` folder\n",
        "On your Mac, zip your `detection` folder: `zip -r detection.zip detection/`\n",
        "Then upload `detection.zip` in the Colab file sidebar on the left, and run this cell."
      ]
    },
    {
      "cell_type": "code",
      "execution_count": None,
      "metadata": {},
      "outputs": [],
      "source": [
        "!unzip -q detection.zip"
      ]
    },
    {
      "cell_type": "markdown",
      "metadata": {},
      "source": [
        "### 4. Prepare Dataset (Extract YOLO Features)\n",
        "This runs your `prepare_dataset.py` on the Colab GPU. It will take a while!"
      ]
    },
    {
      "cell_type": "code",
      "execution_count": None,
      "metadata": {},
      "outputs": [],
      "source": [
        "!python detection/prepare_dataset.py \\\n",
        "  --accident-dir dataset/Accidents \\\n",
        "  --normal-dir dataset/Normal \\\n",
        "  --output-dir data/processed"
      ]
    },
    {
      "cell_type": "markdown",
      "metadata": {},
      "source": [
        "### 5. Train the LSTM\n",
        "This runs your `train.py`. The `.pth` file will be saved when it finishes."
      ]
    },
    {
      "cell_type": "code",
      "execution_count": None,
      "metadata": {},
      "outputs": [],
      "source": [
        "!python detection/train.py"
      ]
    },
    {
      "cell_type": "markdown",
      "metadata": {},
      "source": [
        "### 6. Download your Model\n",
        "Download `detection/models/saved/lstm_classifier.pth` from the left sidebar and put it on your Mac!"
      ]
    }
  ],
  "metadata": {
    "colab": {
      "provenance": []
    },
    "kernelspec": {
      "display_name": "Python 3",
      "name": "python3"
    },
    "language_info": {
      "name": "python"
    }
  },
  "nbformat": 4,
  "nbformat_minor": 0
}

output_path = "/Users/ayushraj/accident_detection/Train_AI_AIDERS_Colab.ipynb"
with open(output_path, "w") as f:
    json.dump(notebook, f, indent=2)

print(f"Successfully generated {output_path}")
