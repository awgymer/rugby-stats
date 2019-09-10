library(data.table)
library(ggplot2)


setwd('~/git_repos/rugby-stats/')
sqd_colors <- fread('data/wc_team_colors.csv')
sqds <- fread('data/wc_squads_processed.csv')
sqds[,
     .(
       mean_caps=mean(caps, na.rm = T),
       mean_age=mean(days_old/365, na.rm = T)
      ),
     by=c('year')
][order(year)]

wc_countries <- sqds[,.(n_wc=length(unique(year))), by=country]

caps_bplot <- (
  ggplot(sqds, aes(x=country, y=caps)) +
    geom_boxplot() +
    theme_bw()
)

tests <- fread('data/all_matches_83_19.csv')

tier_1 <- c(
  "Argentina", "Australia", "England", "France", "Ireland", "Italy",
  "New Zealand", "Scotland", "South Africa", "Wales"
)
tier_2 <- c(
  "Canada", "Fiji", "Georgia", "Japan", "Namibia", "Portugal",
  "Romania", "Russia", "Samoa", "Spain", "Tonga", "United States", "Uruguay"
)

ggplot(
  tests[team %in% wc_countries[,country]][order(year)],
  aes(x=year, y=total_matches)
) +
  geom_point(aes(colour=team)) +
  geom_smooth() +
  theme_bw()
