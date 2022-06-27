#!/usr/bin/perl

($#ARGV >=0 and $#ARGV < 2) or die "invalid arguments";

if($#ARGV==1)
{
    ($ARGV[1] =~ /-b/ or $ARGV[1] =~ /-t=.*/) or die "invalid arguments";
}

@files = qx(ls $ARGV[0]);


print "@files";