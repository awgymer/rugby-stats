library(data.table)
library(plotly)
library(glue)

# Load Natural Earth map units data - converted to GeoJSON using `mapshaper` 
boundaries <- rjson::fromJSON(
  file='../../../../map-data/rugby_borders_geo.json')

geodat <- fread('../data/first_match_with_geo.csv')

# Remove East Germany
geodat <- geodat[team_name != 'East Germany']
gms <- geodat[, 
  .(geounit=unlist(tstrsplit(geounits, ",", fixed=TRUE))), 
  by=setdiff(colnames(geodat), 'geounits')
]

setorder(gms, ko_time)
gms[, ko_sec := ko_time/1000]
gms[, ko_date := as.Date(as.POSIXct(ko_sec, origin='1970-01-01', tz = 'UTC'), tz='UTC')]
gms[, end_date := shift(ko_date, type='lead', fill=Sys.Date()) ,by=geounit]

# Handle end dates for breakup of multi-nation states
# Set the end date for teams of USSR that have not played since to be first game for Russia
russ_start <- gms[team_name == 'Russia', ko_date]
gms[team_name == 'USSR', end_date := min(russ_start, end_date), by=geounit]

# Set Yugoslavian end date to '91 breakup of Yugoslavia for everyone except Serbia & Montenegro and Kosovo
yugoslav_breakup1 <- as.Date('1991-10-08', format='%Y-%m-%d', tz='UTC')
ex_yugoslavs <- c("BIH", "HRV", "MKD", "SVN")
gms[team_name == 'Yugoslavia' & geounit %in% ex_yugoslavs, end_date := min(yugoslav_breakup1, end_date), by=geounit]
ex_yugoslavs2 <- c("MNE", "SRB")
yugoslav_breakup2 <- as.Date('2006-06-03', format='%Y-%m-%d', tz='UTC')
gms[team_name == 'Yugoslavia' & geounit %in% ex_yugoslavs2, end_date := min(yugoslav_breakup2, end_date), by=geounit]
kosovo_ind <- as.Date('2008-02-17', format='%Y-%m-%d', tz='UTC')
gms[team_name == 'Yugoslavia' & geounit == "KOS", end_date := min(kosovo_ind, end_date), by=geounit]

# Set the end date for Czechoslovakia to 1 Jan 93 - dissolution of the state
end_czslo <- as.Date('1993-01-01', format='%Y-%m-%d', tz='UTC')
gms[team_name == 'Czechoslovakia', end_date := min(end_czslo, end_date), by=geounit]

# Set the end date for Arab Gulf countries to the breakup of that Union
end_arabian_gulf <- as.Date('2010-05-31', format='%Y-%m-%d', tz='UTC')
gms[team_name == 'Arabian Gulf', end_date := min(end_arabian_gulf, end_date), by=geounit]

# Get the end and start years
gms[, ko_year := as.numeric(format(ko_date, '%Y'))]
gms[, end_year := as.numeric(format(end_date, '%Y'))]
gms[, year := ko_year]

# Create all year/geounit combinations as a data.table
all_years <- seq(1870, 2020)
all_geos <- as.data.table(transpose(
  lapply(boundaries$features, function(x){ 
    c(x$properties$GU_A3, x$properties$GEOUNIT, x$properties$SOVEREIGNT, x$properties$centroid$lon, x$properties$centroid$lat) 
  })
))
setnames(all_geos, c('V1', 'V2', 'V3', 'V4', 'V5'), c('geounit', 'geoname', 'sovname', 'clon', 'clat'))
# Fix for Kazakhstan mislabelling!
all_geos[sovname=='Kazakhstan', geoname := sovname]
all_idx <- CJ(all_geos[['geounit']], all_years, unique=TRUE)
setnames(all_idx, c('V1', 'all_years'), c('geounit', 'year'))
setorder(all_idx, year)

# Set keys for all_geos and idx tables - must key of geounit THEN year
setkey(all_idx, geounit, year)
setkey(all_geos, geounit)
all_idx <- all_geos[all_idx]
setkey(all_idx, geounit, year)
# Perform a forward rolling join
# fills missing data for years after first game
setkey(gms, geounit, year)
rolld_gms <- gms[all_idx, roll=T]
# If a team stopped playing then set their values for years after that to NA
rolld_gms[end_year<year, setdiff(colnames(rolld_gms), colnames(all_idx)) := NA]
rolld_gms[,statename := ifelse(geoname==sovname, geoname, glue_data(.SD, '{geoname} ({sovname})'))]
rolld_gms[, years_played := year-ko_year]
# Create scaled values for length of time played to be used for colouring
# Then set NA (not played) to -1
rolld_gms[, colorscale := scales::rescale(years_played)]
rolld_gms[is.na(colorscale), colorscale := -1]

fwrite(rolld_gms, '../data/first_match_plot_data.csv')

