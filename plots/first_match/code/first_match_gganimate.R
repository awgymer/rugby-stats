library(data.table)
library(ggplot2)
library(maps)
library(gganimate)

first_gms <- fread('../data/first_match.csv')
corrects <- fread('../data/old_country_correct.csv')
corrects <- corrects[, lapply(.SD, function(x) unlist(tstrsplit(x, ",", fixed=TRUE))), by ="team_id", .SDcols=c("locales")]

first_gms[, ko_sec:=ko_time/1000]
first_gms <- corrects[first_gms, on="team_id"]
first_gms[is.na(locales), locales:=name]
first_gms[, ko_date:=as.Date(as.POSIXct(ko_sec, origin='1970-01-01', tz = 'UTC'), 'UTC')]

# Remove East Germany - rugby was played there before it existed, and is still played there now
first_gms <- first_gms[team_name != 'East Germany']
# Add end dates for those teams that no longer exist
first_gms[order(ko_date), end_date:=shift(ko_date, type='lead', fill=Sys.Date()) ,by=locales]

all_dates <- first_gms[,.(reldate=unique(first_gms[['ko_date']])),by="team_id,locales"]
expanded_gms <- all_dates[first_gms, on=c(team_id="team_id", locales="locales")]
expanded_gms <- expanded_gms[reldate>=ko_date & reldate < end_date]
expanded_gms[,age:=reldate-ko_date]

worldmap <- as.data.table(map_data('world'))

worlddates <- worldmap[, .(reldate=unique(first_gms[['ko_date']])), by=order] 
expanded_world <- worlddates[worldmap, on="order"]

w1 <- expanded_gms[expanded_world, on=c(locales='region', reldate='reldate')]
w1[expanded_gms, c('ko_date', 'name', 'age') := list(i.ko_date, i.name, i.age), on=c(reldate='reldate', subregion='locales')]
w1 <- w1[!is.na(ko_date)]

world <- ggplot() +
  borders("world", colour = "gray85", fill = "gray80") +
  ggthemes::theme_map() 

map <- world + geom_polygon(data=w1[order(order)], aes(x=long, y=lat, group=paste0(group, reldate), fill=as.numeric(age))) 

ani <-  (
  map + 
    labs(title = 'Date: {frame_time}') + 
    transition_time(reldate) +
    scale_fill_gradient(high='#236B1E', low='#bdd2bb')
)
