```
dx run swiss-army-knife -icmd="cd /home/dnanexus; docker load -i /mnt/project/fema_ukb.tar; docker run -v /home/dnanexus/out:/home/dnanexus/out -v /mnt/project:/mnt/project fema_ukb /mnt/project/Cov_Metabolomics.csv /mnt/project/Data_Metabolomics.csv /home/dnanexus/out/out/ OutFile_SAK.mat;" --destination allOutputs
```