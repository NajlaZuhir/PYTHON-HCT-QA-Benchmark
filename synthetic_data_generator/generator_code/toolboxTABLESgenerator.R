
### toolbox for TABLE GENERATION

# --------------------------------------------------------------------------------------------------
# STEP 1: Get Names and Values
# Description: Retrieves the 'names' and 'values' for a given attribute code from semantic data.
# get the names and values of attribute code from semantic data
getNamesValues <- function(semanticData,code){
  for (i in 1: length(semanticData)){
    if (semanticData[[i]]$code == code) { 
      res <- NULL
      res$names = semanticData[[i]]$names
      res$values = semanticData[[i]]$values
      return(res)
    }
  }
  return(NULL)
}

#--Test Data------------------------------------------------------------------------------------------
# semanticData <- list(
#   list(code = "x1", names = c("country"), values = c("USA", "UK")),
#   list(code = "x2", names = c("year"), values = c(2020, 2021))
# )
# getNamesValues(semanticData, "x1")


# generate samples for the value column
# ensure integer values are distinct
# valueCode can be a code for values as in semantics or directly an interval of values
# use dot like in 2.3 and 24.0 to identify a real number and no dot like 24 to identify integers
# any interval containing at least a real as min or max will generate real numbers uniformly sampled in that interval

# --------------------------------------------------------------------------------------------------
# STEP 2: Make Distinct
# Description: Ensures uniqueness by adding a small offset to duplicate values.

# generate distinct values from a list of values by adding epsilon offsetwith numDigits decimal values
# to each duplicate, then randomize their order
makeDistinct <- function(vals,numDigits){
  #print("makeDistinct")
  #print(vals)
  while (length(unique(vals))!=length(vals)){
    # there are still duplicates
    svals = sort(vals) 
    for (i in which(diff(svals)==0)){
      # add the smallest possible value to each duplicate
      svals[i+1] = svals[i+1]+10^(-numDigits)
    }
    vals = svals
  }
  
  # return randomize order
  return(sample(vals)) 
}


# --------------------------------------------------------------------------------------------------
# STEP 3: Get Sample Values (Numeric)
# Description: Generates samples from semantic ranges (integer or real values).
getSampleValues <- function(semanticValues,valueCode,numSample,numDigits=2){
  
  if (length(valueCode) == 1){ # valueCode is a name of a code like "int100" in semanticValues to generate values 
    for (cn in names(semanticValues)){
      if (cn == valueCode) { 
        rangeVal = unlist(semanticValues[[cn]])
        sv1 = semanticValues[[cn]][[1]]
        sv2 = semanticValues[[cn]][[2]]
        
        if (is.integer(sv1) && is.integer(sv2)) {
          minv = rangeVal[1]
          maxv = max(minv+numSample,rangeVal[2])
          vals = sample(minv:maxv,numSample,replace = FALSE) # ensure numSample distinct values are generated
        } else {
          vals = round(runif(numSample,min = rangeVal[1],max = rangeVal[2]), digits = numDigits)
        }
      }
    }
  }else{
    
    # valueCode is directly a list of two values min and max: c(m,M) given in the field "values" of the table json format
    rangeVal = unlist(valueCode)
    sv1 = valueCode[[1]]
    sv2 = valueCode[[2]]
    
    if (is.integer(sv1) && is.integer(sv2)) {
      minv = rangeVal[1]
      maxv = max(minv+numSample,rangeVal[2])
      vals = sample(minv:maxv,numSample,replace = FALSE) # ensure numSample distinct values are generated
    } else {
      vals = round(runif(numSample,min = rangeVal[1],max = rangeVal[2]), digits = numDigits)
    }
  }
  vals = makeDistinct(vals,numDigits)
  return(vals)
}


#--Test Data------------------------------------------------------------------------------------------
# semanticValues <- list(int5 = c(1L, 5L))
# set.seed(123)
# getSampleValues(semanticValues, "int5", numSample = 3, numDigits = 0)


# --------------------------------------------------------------------------------------------------
# STEP 4: Get Values From Names
# Description: Extracts attribute values based on inclusion/exclusion filters.
# get the values of attribute from their names and filters
getValuesFromNames <- function(namesAndValues,valKeep,valRemove){
  speStr = "!@!" # special sep to distinguish numbers of the names and numbers added when unlisting
  nam = namesAndValues$names
  val = namesAndValues$values
  if (length(nam)>1){
    
    # if names contain numbers, add a character at the end to allow proper clean up
    for (ii in 1:length(val)){
      curname = names(val[[ii]])
      names(val[[ii]]) = paste0(curname,speStr)
    }
    
    # TREE 
    uval=unlist(val) # it adds numbers at the end of the names to avoid duplicates
    # remove numbers after speStr
    cleanuval = gsub(speStr, '',gsub(paste0(speStr,'[[:digit:]]+'), '',names(uval)))
    cleanvalues = paste0(cleanuval,'.',uval)
    sepvalues = strsplit(cleanvalues,split = "\\.")
    
    Ltmp <- NULL
    # apply filter
    noFilter = TRUE
    # keep (priority over remove list, remove list will not be considered if keep list is used)
    if (length(valKeep)>0) {
      for (fi in 1:length(valKeep)){
        keepval = valKeep[fi]
        for (gi in 1:length(sepvalues)){
          if (any(sepvalues[[gi]] == keepval)) Ltmp <- rbind(Ltmp, paste(sepvalues[[gi]],collapse="."))
        }
      }
      noFilter = FALSE
    }
    # remove (remove list ONLY considered if keep list not present
    if (length(valRemove)>0 && length(valKeep)==0) {
      for (fi in 1:length(valRemove)){
        removeval = valRemove[fi]
        for (gi in 1:length(sepvalues)){
          if (all(sepvalues[[gi]] != removeval)) Ltmp <- rbind(Ltmp, paste(sepvalues[[gi]],collapse="."))
        }
      }
      noFilter = FALSE
    }
    
    
    # generate all data
    if (noFilter) {
      Ltmp <- cleanvalues
    }
    
    
  } else {
    # NOT A TREE, SINGLE ATTRIBUTE
    uval=unlist(val)
    
    Ltmp <- NULL
    # apply filter
    noFilter = TRUE
    # keep (priority over remove list, remove list will not be considered if keep list is used)
    if (length(valKeep)>0) {
      for (fi in 1:length(valKeep)){
        keepval = valKeep[fi]
        for (gi in 1:length(uval)){
          if (uval[gi] == keepval) Ltmp <- rbind(Ltmp, uval[gi])
        }
      }
      noFilter = FALSE
    }
    # remove (remove list ONLY considered if keep list not present
    if (length(valRemove)>0 && length(valKeep)==0) {
      for (fi in 1:length(valRemove)){
        removeval = valRemove[fi]
        for (gi in 1:length(uval)){
          if (uval[gi] != removeval) Ltmp <- rbind(Ltmp, uval[gi])
        }
      }
      noFilter = FALSE
    }
    
    
    # generate all data
    if (noFilter) {
      Ltmp <- uval
    }
    
  }
  
  return(Ltmp)
}


# -- Test Case --
# namesAndValues <- list(
#   names = c("country", "year"),
#   values = list(
#     country = c("USA", "UK"),
#     year = c(2020, 2021)
#   )
# )
# print(getValuesFromNames(namesAndValues, c(), c()))
# print(getValuesFromNames(namesAndValues, c("UK"), c()))
# print(getValuesFromNames(namesAndValues, c(), c("USA")))


# --------------------------------------------------------------------------------------------------
# STEP 5: Sample Values from List
# Description: Randomly selects consecutive values from a list.

# sample values from filtered list
# use valSample = [0] to pick all existing values without sampling
# pick between valSample[1] and valSample[2] consecutive values in valList list of values
# for instance: in [1,2,3,4,5] pick [2,4] can generate at random either: [1,2],[2,3],[3,4],[4,5],[1,2,3],[2,3,4],[3,4,5],[1,2,3,4],[2,3,4,5]
sampleValues <- function(valList,valSample){
  # sample
  Ltmp = valList
  if (length(valSample)==2) {
    ## DO SAMPLING [n,m] means: pick between n and m consecutive values in current list of values
    n = valSample[1]
    m = valSample[2]
    numVal = length(valList)
    n = max(1,min(n,numVal)) # make sure 1 <= n <= numVal
    m = max(n,min(m,numVal)) # make sure n <= m <= numVal
    if (n==m) { siz = n } else { siz = sample(n:m,1) } # rand number between n and m
    pos = sample(1:(numVal-siz+1),1) # rand position between 1 and numVal-siz+1
    ind = pos:(pos+siz-1) # list of index to sample from current list of values
    Ltmp <- valList[ind]
  }
  
  isAggPossible = "true"
  if (length(Ltmp)==1) isAggPossible = "false"
  
  res <-NULL
  res$isAggPossible <- isAggPossible
  res$listAttrNames <- Ltmp
  
  return(res)
}
# -- Test the function --
# set.seed(123)
# valList <- c("A", "B", "C", "D", "E")
# valSample <- c(2, 3)

# print(sampleValues(valList, valSample))



# --------------------------------------------------------------------------------------------------
# STEP 6: Sample Values From Hierarchical Names
# Description: Samples attribute names across multiple hierarchy levels.

## generate samples follwoing valSample (use sampleValues internally)
## with listCompositeAttrNames a list of attribute names made of nested levels separated by "."
## sampling is done on each branch at each level independently
sampleValuesFromHierarchy <- function(listCompositeAttrNames,valSample){
  
  
  # it has added '.' between level names
  LattrAllLevels = strsplit(listCompositeAttrNames,split="\\.")
  
  depthAttr = length(LattrAllLevels[[1]])
  
  # for parent level, sample which to keep
  MattrAllLevelsINI = matrix("",length(LattrAllLevels),depthAttr)
  
  for (ii in 1:depthAttr){
    # get parent
    for (jj in 1:length(LattrAllLevels)){
      MattrAllLevelsINI[jj,ii] = LattrAllLevels[[jj]][ii] 
    }
  }
  MattrAllLevels = MattrAllLevelsINI
  # sample level 1
  attLev = MattrAllLevels[,1]
  uAttLev = unique(attLev)
  
  
  if (length(valSample)==2) {
    
    res = sampleValues(uAttLev,valSample)
    splAttLev = res$listAttrNames
    
    # record if it is possible to aggregate several attribute values at that level
    isAggPossible <- NULL
    isAggPossible[1] = res$isAggPossible
    #if (length(splAttLev)==1) isAggPossible[1] = "false" # a single attribute value at that level, no aggregate
    
    MattrAllLevels = MattrAllLevels[attLev %in% splAttLev,]
    
    for (ii in 2:depthAttr){
      upar = unique(MattrAllLevels[,1])
      lupar = length(upar)
      subMattrAllLevels = NULL
      isAggPossible[ii] = "true"
      for (ipar in 1:lupar){
        curpar = upar[ipar]
        attLev = MattrAllLevels[MattrAllLevels[,1]==curpar,,drop = F]
        uAttLev = unique(attLev[,2])
        res = sampleValues(uAttLev,valSample)
        splAttLev = res$listAttrNames
        if (res$isAggPossible == "false") isAggPossible[ii] = "false"
        subMattrAllLevels = rbind(subMattrAllLevels, attLev[attLev[,2] %in% splAttLev,])
      }
      # concatenate current and parent column
      Lcollapsed = NULL
      for (ipr in 1:nrow(subMattrAllLevels)){
        Lcollapsed[ipr] = paste0(subMattrAllLevels[ipr,1:2],collapse=".")
      }
      if (ncol(subMattrAllLevels)>2){
        MattrAllLevels=cbind(Lcollapsed,subMattrAllLevels[,3:ncol(subMattrAllLevels)])
      } else {
        MattrAllLevels=matrix(Lcollapsed,nrow(subMattrAllLevels),1)
        break
      }
    }
    res <-NULL
    res$isAggPossible <- paste0(isAggPossible,collapse=".")
    res$listAttrNames <- c(MattrAllLevels)
    return(res)
    
  } else {
    
    # record if it is possible to aggregate several attribute values at that level
    isAggPossible <- NULL
    isAggPossible[1] = "true"
    if (length(uAttLev)==1) isAggPossible[1] = "false" # a single attribute value at that level, no aggregate
    
    
    for (ii in 2:depthAttr){
      upar = unique(MattrAllLevels[,1])
      lupar = length(upar)
      subMattrAllLevels = NULL
      isAggPossible[ii] = "true"
      for (ipar in 1:lupar){
        curpar = upar[ipar]
        attLev = MattrAllLevels[MattrAllLevels[,1]==curpar,,drop = F]
        uAttLev = unique(attLev[,2])
        if (length(uAttLev)==1) isAggPossible[ii] = "false"
        subMattrAllLevels = rbind(subMattrAllLevels, attLev[attLev[,2] %in% uAttLev,])
      }
      # concatenate current and parent column
      Lcollapsed = NULL
      for (ipr in 1:nrow(subMattrAllLevels)){
        Lcollapsed[ipr] = paste0(subMattrAllLevels[ipr,1:2],collapse=".")
      }
      if (ncol(subMattrAllLevels)>2){
        MattrAllLevels=cbind(Lcollapsed,subMattrAllLevels[,3:ncol(subMattrAllLevels)])
      } else {
        MattrAllLevels=matrix(Lcollapsed,nrow(subMattrAllLevels),1)
        break
      }
    }
    res <-NULL
    res$isAggPossible <- paste0(isAggPossible,collapse=".")
    res$listAttrNames <- listCompositeAttrNames
    return(res)
  }
}

# -- Test Case --
# compositeAttrs <- c("Asia.India.Delhi", "Asia.India.Mumbai", "Europe.Germany.Berlin")
# valSample <- c(1, 2)
# set.seed(123)
# print(sampleValuesFromHierarchy(compositeAttrs, valSample))


# --------------------------------------------------------------------------------------------------
# STEP 7: Get Attribute Index from Code
# Description: Returns the index of the attribute code in the attribute list.

# get index of col/row attribute having a certain code (return the first one if a list of codes is given) 
getAttrFromCodes <- function(attrList,codes){ 
  for (i in 1:length(attrList)) if (is.element(attrList[[i]]$code,codes)) return(i)
} 


# -- Test Case --
# attrList <- list(
#   list(code = "x1", names = c("Country")),
#   list(code = "x2", names = c("Year")),
#   list(code = "x3", names = c("City"))
# )
# print(getAttrFromCodes(attrList, "x2"))   # Expected: 2
# print(getAttrFromCodes(attrList, "x99"))  # Expected: NULL


# --------------------------------------------------------------------------------------------------
# STEP 8: Get Codes from Name
# Description: Maps attribute names to their codes based on semantic metadata.

getCodesFromName <- function(allSemanticAttributes,attrName){
  attrData <- allSemanticAttributes$data
  codes <- NULL
  for (i in 1:length(attrData)) if (is.element(attrName,unlist(attrData[[i]]$names))) codes <- c(codes,attrData[[i]]$code)
  return(codes)
}

# -- Test Case --
# semanticData <- list(
#   data = list(
#     list(code = "x1", names = c("Country")),
#     list(code = "x2", names = c("Year")),
#     list(code = "x3", names = c("City"))
#   )
# )
# print(getCodesFromName(semanticData, "Year"))     # Expected: "x2"
# print(getCodesFromName(semanticData, "Unknown"))  # Expected: NULL

#  Final Test (R) — Full Flow ----------------------------------
# Load your toolbox
source("toolboxTablesgenerator.R")

# Step 1: Mock semanticData
semanticData <- list(
  list(code = "x1", names = c("Country"), values = list(Country = c("USA", "UK", "Qatar"))),
  list(code = "x2", names = c("Year"), values = list(Year = c(2020, 2021, 2022)))
)

# Step 1: Get names/values
nv <- getNamesValues(semanticData, "x1")

# Step 2 & 3: Filter values
filtered_vals <- getValuesFromNames(nv, valKeep = c(), valRemove = c("UK"))

# Step 4: Sample flat values
sample_cfg <- c(1, 2)
sampled <- sampleValues(filtered_vals, sample_cfg)

# Step 5: Hierarchical test
compositeAttrs <- c(
  "Asia.Qatar.Doha", "Asia.Qatar.AlRayyan", "Asia.UAE.Dubai",
  "Europe.UK.London", "Europe.UK.Manchester"
)
set.seed(123)
hct_result <- sampleValuesFromHierarchy(compositeAttrs, sample_cfg)

# Step 6: Get index of attribute
attr_index <- getAttrFromCodes(semanticData, "x2")

# Step 7: Get code from name
semanticDataObj <- list(data = semanticData)
code_result <- getCodesFromName(semanticDataObj, "Country")

# Show results
cat("🔹 Filtered:", filtered_vals, "\n")
print(sampled)
print(hct_result)
cat("🔹 Attribute Index for 'x2':", attr_index, "\n")
cat("🔹 Code for 'Country':", code_result, "\n")
