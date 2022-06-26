#!/usr/bin/perl 

$path = shift or die "rip\n";

open($fh, "<", $path) or die "Percorso non trovato\n";

%mac_user = ();
while(<$fh>)
{
    /^(.*)#(.*)$/;
    $mac_user{uc $1}= $2;
}
close($fh);

@arp_lines = qx(arp -an);

%mac_ip= ();
%user_online=();
%user_offline=();

for(@arp_lines)
{
    if(/^.*\(((\d{1,3}\.){3}\d{1,3})\).*((\w{2}:){5}\w{2}).*$/)
    {
        $mac_ip{uc $3} = $1;
        $mac =uc $3;
        if(qx(ping -c1 $1) =~ /100% packet loss/)
        {
            if(exists $mac_user{$mac})
            {
                $user_offline{$mac_user{$mac}}= "SIUM";
            }
        }
        else
        {
            if(exists $mac_user{$mac})
            {
                $user_online{$mac_user{$mac}}= "SIUM";
            }
        }
    }
}
    print "######## Online users #########\n";
    foreach $nome(sort {$a cmp $b} keys %user_online)
    {
        print "$nome\n";
    }
    print "######## Offline users #########\n";
    foreach $nome(sort {$b cmp $a} keys %user_offline)
    {
        print "$nome\n";
    }

##/home/ciccio/Desktop/mac_addresses.txt