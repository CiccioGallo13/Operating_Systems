#!/usr/bin/perl

($#ARGV >=0 and $#ARGV < 2) or die "invalid arguments";

if($#ARGV==1)
{
    ($ARGV[1] =~ /-b/ or $ARGV[1] =~ /-t=.*/) or die "invalid arguments";
}

@stat = qx(stat $ARGV[0]);
$stat[1] =~ /directory/ or die "not a directory";
@files = qx(ls $ARGV[0]);
%size_name = ();
$filetag = ".*";
if($ARGV[1] =~ /-t=(.*)/)
{
    $filetag = $1;
}

$sizeF = 0;
%name_size=();
while(<@files>)
{   $filename = $_;
    @stat = qx(stat $ARGV[0]/$filename);
    if(not($stat[1] =~ /directory/) and $stat[1] =~ /$filetag$/)
    {   
        $stat[1] =~ /Blocks: (\d+)\s+ IO Block: (\d+)/;
        $size_name{$1*$2} = $filename;
        $name_size{$filename} = $1*$2;
        $sizeF += $1*$2;
    }
}
if($#ARGV == 0 || $ARGV[1] =~ /-t/)
{
    use List::MoreUtils qw( minmax );
    ($min, $max)= minmax (keys %size_name);
    print "SizeFolder della cartella $ARGV[0] = $sizeF\n";
    print "Max: $size_name{$max} ---> $max\n";
    print "Min: $size_name{$min} ---> $min\n";
}
elsif($ARGV[1] =~ /-b/)
{
    open($fh, ">", "output.log");
    foreach(sort {($name_size{$b} <=> $name_size{$a}) || $a cmp $b} keys %name_size )
    {
        print $fh "$_ --> $name_size{$_}\n";
    }
    close($fh);
}

