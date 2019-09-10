library(data.table)
library(ggplot2)
library(gganimate)
library(reshape2)
library(jsonlite)

library(shiny)
library(plotly)

## Function to get the upper triangle of the correlation matrix
get_upper_tri <- function(cormat){
  cormat[lower.tri(cormat)]<- NA
  return(cormat)
}

## Load the data from the JSON (list column)
all_tests <- as.data.table(fromJSON('test_scores.json'))

## Example of how to filter series (list column)
#all_tests[mapply('%in%', 'Six Nations', series),]

## A count of the grouped unique scores
#all_tests[, .(total=.N), by='winning_score,losing_score']

## Calculate the highest score
high_score <- max(all_tests[,winning_score])

## Make a matrix of the scores
score_tab <- table(
  factor(all_tests[,losing_score], levels=0:high_score), 
  factor(all_tests[,winning_score], levels=0:high_score)
)

## Just take the upper triangle (lower should be empty anyway)
upper_tri <- get_upper_tri(score_tab)

## Melt the matrix
long_scores <- melt(
  upper_tri, 
  varnames = c('losing_score', 'winning_score'), 
  value.name = 'occurences', na.rm=T
)

## Plot the heatmap
p <- ggplot(
  long_scores, aes(x=winning_score, y=losing_score, fill=occurences)
) + 
scale_fill_gradient(
  low = "lightblue", high = "navy", na.value='grey98', limits =  c(1,61)
) + 
geom_tile(color='gray50') + theme_minimal() + 
geom_text(
  data=subset(long_scores, occurences==0 & (winning_score %in% c(1,2,4) | losing_score %in% c(1,2,4))),
  aes(label='x', color='red'), show.legend=F, lineheight=1, size=1.2,
  nudge_y=0.2
) + coord_fixed()

df('test_scores.pdf')
p
dev.off()

