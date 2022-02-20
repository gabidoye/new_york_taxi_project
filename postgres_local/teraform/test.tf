terraform {
  required_providers {
    google = {
      source = "hashicorp/google"
    }
  }
}

provider "google" {
  credentials = file("/Users/gabidoye/Downloads/dataengineering-bizzy-770f13466383.json")

  project = "dataengineering-bizzy"
  region  = "us-central1"
  zone    = "us-central1-c"
}

resource "google_compute_instance" "default" {
  name         = "test"
  machine_type = "e2-medium"
  zone         = "us-central1-c"

  tags = ["foo", "bar"]

  boot_disk {
    initialize_params {
      image = "debian-cloud/debian-9"
    }
  }

  network_interface {
    network = "default"

    access_config {
      // Ephemeral public IP
    }
  }

  metadata = {
    foo = "bar"
  }

  metadata_startup_script = "echo hi > /test.txt"
}

resource "google_bigquery_dataset" "dataset" {
  dataset_id = "BQ_DATASET"
  project    = "dataengineering-bizzy"
  location   = "us-central1"
}


resource "google_storage_bucket" "data-lake-bucket" {
  name          = "data_lake_bucke0075" # Concatenating DL bucket & Project name for unique naming
  location      = "us-central1"

  # Optional, but recommended settings:
  storage_class = "STANDARD"
  uniform_bucket_level_access = true

  versioning {
    enabled     = true
  }

  lifecycle_rule {
    action {
      type = "Delete"
    }
    condition {
      age = 30  // days
    }
  }

  force_destroy = true
}
