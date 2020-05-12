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
