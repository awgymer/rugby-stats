sqds[player %like% '\\(c\\)', captain := T]
sqds[,.(age=mean(days_old, na.rm=T)/365), by='year,country,captain']

capt_ages <- dcast(sqds[,.(age=mean(days_old, na.rm=T)/365), by='year,country,captain'], year + country ~ captain, value.var = 'age')

setnames(capt_ages, c('year', 'country', 'squad', 'captain'))

ggplot(capt_ages, aes(y = country, x=squad, xend=captain, color = ifelse(captain>squad, 'red', 'black'))) + 
  geom_dumbbell(colour_xend = 'red', colour_x = 'blue') + 
  theme_bw() + 
  facet_wrap(~year)

ggplot(sqds, aes(x=days_old/365, y=caps, colour=captain)) + 
  geom_point(aes(alpha = captain)) + 
  scale_alpha_manual(values = c(0.2, 1.0)) + 
  scale_colour_manual(values=c("#666666", "#FF0000")) +
  theme_bw()