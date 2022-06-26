#!/usr/bin/perl

$ARGV[0] =~ /.+\.log/ or die "Non hai inserito un file di log";
($ARGV[1] <= $ARGV[2] and $ARGV[2] < 24 and $#ARGV==2) or die "Non hai inserito un intevallo valido";

%udp=();
%flags=();

open($fh, "<", $ARGV[0]);

while(<$fh>)
{
    /((\d\d)[\d:\.]+) IP ([\d\.>\s]+): ([A-Z]+).*/;
    if($2>=$ARGV[1] and $2 <= $ARGV[2])
    {
        $time = $1;
        $ip_port = $3;
        if($4 =~ /UDP/)
        {
            $udp{$time} = $ip_port;
        }
        else
        {
            $flags{$time} = $ip_port;
        }
    }
}
close($fh);

open($udp_log, ">", "udp.log");
foreach(sort{$a cmp $b} keys %udp)
{
    print $udp_log "$_ --> $udp{$_}\n";
}
$tmp = keys %udp;
print $udp_log "Totale: $tmp";
close($udp_log);

open($flags_log, ">", "flags.log");
foreach(sort{$b cmp $a} keys %flags)
{
    print $flags_log "$_ --> $flags{$_}\n"
}
$tmp = keys %flags;
print $flags_log "Totale: $tmp";
close($flags_log);