###########################################################################
## RDROBUST R Package
## Do-file for Empirical Illustration
## Authors: Sebastian Calonico, Matias D. Cattaneo, Max H. Farrell and Rocio Titiunik 
###########################################################################
### Clear R environment
rm(list=ls(all=TRUE))

### Install R library
### NOTE: depending on your system, you may need to do it as root
#install.packages('rdrobust')

library(rdrobust)
library(ggplot2)

### Load RDROBUST package
data = read.csv("rdrobust_senate.csv")
y = data$vote
x = data$margin
c = 0

###########################################################################
# Generate input data for output plot
###########################################################################
plot1 = rdplot(y,x, ci=95, hide=TRUE)
rdplot_mean_bin = plot1$vars_bins[,"rdplot_mean_bin"]
rdplot_mean_y   = plot1$vars_bins[,"rdplot_mean_y"]
y_hat           = plot1$vars_poly[,"rdplot_y"]
x_plot          = plot1$vars_poly[,"rdplot_x"]
rdplot_cil_bin =  plot1$vars_bins[,"rdplot_ci_l"]
rdplot_cir_bin =  plot1$vars_bins[,"rdplot_ci_r"]
rdplot_mean_bin=  plot1$vars_bins[,"rdplot_mean_bin"]
y_hat_r=y_hat[x_plot>=c]
y_hat_l=y_hat[x_plot<c]
x_plot_r=x_plot[x_plot>=c]
x_plot_l=x_plot[x_plot<c]

col.lines = "blue"
col.dots  = 1
type.dots = 20
title="RD Plot"
x.label="X axis"
y.label="Y axis"
x.lim=c(min(x, na.rm=T),max(x, na.rm=T))
y.lim=c(min(y, na.rm=T), max(y, na.rm=T))


###########################################################################
# Generate rdplot using ggplot2
###########################################################################
temp_plot <- ggplot() + theme_bw() +
  geom_point( aes(x = rdplot_mean_bin, y = rdplot_mean_y), col = col.dots, na.rm = TRUE) +
  geom_line(  aes(x = x_plot_l, y = y_hat_l), col = col.lines, na.rm = TRUE) +
  geom_line(  aes(x = x_plot_r, y = y_hat_r), col = col.lines, na.rm = TRUE) +
  labs(x = x.label, y = y.label) + ggtitle(title) +
  labs(title = title, y = y.label, x = x.label) +
  coord_cartesian(xlim = x.lim, ylim = y.lim) +
  theme(legend.position = "None") +
  geom_vline(xintercept = c, linewidth = 0.5)
temp_plot

## Add confidence intervals 
temp_plot <- temp_plot +
  geom_errorbar(aes(x = rdplot_mean_bin, ymin = rdplot_cil_bin, ymax = rdplot_cir_bin), linetype = 1) 
temp_plot

# Shade
temp_plot <- temp_plot +
  geom_ribbon(aes(x = rdplot_mean_bin, ymin = rdplot_cil_bin, ymax = rdplot_cir_bin))
temp_plot

###########################################################################
# Generate rdplot using base plot (RDPLOT backward compatibility)
###########################################################################
plot(rdplot_mean_bin, rdplot_mean_y, 
     main = title, xlab = x.label, ylab = y.label, 
     ylim = y.lim, xlim = x.lim, col = col.dots, pch = type.dots)
lines(x_plot_l, y_hat_l, type = "l", col = col.lines) 
lines(x_plot_r, y_hat_r, type = "l", col = col.lines) 
abline(v=c)

## Add confidence intervals      
arrows(x0=rdplot_mean_bin, y0=rdplot_cil_bin, x1=rdplot_mean_bin, y1=rdplot_cir_bin, 
       code = 3, length = 0.1, angle = 90, col = 'grey')

# Add shade  
polygon(c(rev(rdplot_mean_bin),rdplot_mean_bin),c(rev(rdplot_cil_bin),rdplot_cir_bin), col = "grey75")      


