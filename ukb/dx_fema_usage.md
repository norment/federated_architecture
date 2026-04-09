# Command to launch the workstation

```
dx run app-cloud_workstation --ssh
```

# Borrowed from the documentation – makes sure we are in the right place

```
unset DX_WORKSPACE_ID
dx cd $DX_PROJECT_CONTEXT_ID:
```
 

# Download Docker image fema_ukb.tar

```
dx download fema_ukb.tar
``` 

# Download required files

```
dx download test_covarFile_65000obs_25X_68y.csv
dx download test_phenFile_65000obs_25X_68y.csv
``` 

# Load Docker image

```
docker load -i /home/dnanexus/fema_ukb.tar
```

# Run analysis

```
docker run -v /home/dnanexus/:/home/dnanexus fema_ukb /home/dnanexus/test_covarFile_65000obs_25X_68y.csv /home/dnanexus/test_phenFile_65000obs_25X_68y.csv /home/dnanexus/ analysis_synData_65000obs_25X_68y_2.mat
```
 

# Then, the output file needs to be “pushed” out

```
dx upload /home/dnanexus/analysis_synData_65000obs_25X_68y_2.mat
```
 
# Kill the session

```
dx terminate $DX_JOB_ID
```
