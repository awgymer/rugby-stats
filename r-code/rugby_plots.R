library(glue)
legend_bottom <- theme(legend.position = "bottom")

x_axis_angled <- function(x=305) {
  h = 0
  if(0 <= x & x < 180) {
    h = 1
  }
  theme(axis.text.x = element_text(angle = x, hjust = h))
}

tier_cols <- list(
  muted = list("#95c292", "#9295c2", "#c29295"),
  dark = list("#2c8626", "#262c86", "#86262c"),
  brewer = list("#1b9e77", "#7570b3", "#d95f02")
)

titleize_ <- function(x) {
  paste(toupper(substring(x, 1, 1)), substring(x, 2), sep="", collapse=" ")
}

titleize <- function(x) {
  s <- strsplit(x, " ")
  lapply(s, titleize_)
}

sigfig <- function(vec, digits=3) {
  return(
    gsub("\\.$", "", 
      formatC(signif(vec,digits=digits), digits=digits, format="fg", flag="#")
    )
  )
}

hex_to_rgba <- function(hex, opacity=1) {
  glue("rgba({paste(col2rgb(hex), collapse=',')},{opacity})")
}

get_team_colour_no_white <- function(team, team_cols){
  team_cols[country==team, ifelse(primary!='#ffffff', primary, secondary)]
}

get_team_border_col <- function(team, team_cols){
  team_cols[country==team, ifelse(secondary=='#ffffff', primary, secondary)]
}

get_team_bg_col <- function(team, team_cols){
  team_cols[country==team, primary]
}

get_team_text_col <- function(team, team_cols){
  team_cols[country==team, secondary]
}

get_team_logo <- function(team, team_cols, path='') {
  logo <- team_cols[country==team, logo]
  if(!(length(logo) > 0)){
    logo <- team_cols[country=='unknown', logo]
  }
  return(file.path(path, logo))
}

get_team_flag <- function(team, team_cols, path='') {
  flag <- team_cols[country==team, flag]
  if(!(length(flag) > 0)){
    flag <- team_cols[country=='unknown', flag]
  }
  return(file.path(path, flag))
}
