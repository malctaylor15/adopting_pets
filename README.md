## Petfinder Project   

I am curious to understand adoption rates for dogs and cats. 

I am curious to know the average time until a dog is adopted and if it varies significantly between shelter, dog types, location etc. 


## Process  

First step is to build a pipeline that collects data from petfinder. Petfinder seems like the leading pet adoption app. When I called a few shelters (in the NY region), they directed me to petfinder to see their available pets. Petfinder is also free so there isn't an incentive to not use it, even as an alternative marketing channel. Many shelters seem to have their own sites to fill out the adoption paperwork. 

Once the pipeline is build we can start creating aggregations to understand the flow of pets into and out of the system. We can see average volumes for different animal shelters. We can see if dog characteristics (hair length, size, energy) or location/ shelter affect it's time in the animal shelter. 


Over time, we could compare different area rates to understand the differences in dog areas. 



## Getting Started  

To get started, create an API key at (petfinder)[http://awos.petfinder.com/shelters/developer.html] . It is a pretty simple process. Next we use the petpy library which made getting the datasets very easy. We build a small process around collecting the data adn sending email notifications if anything goes awry.  
