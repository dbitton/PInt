#!/usr/local/bin/perl -w

use strict;
use Data::Dumper;
use DBI;

my $file = "/var/www/htdocs/RFmergedSVMpred_11nov2010_tab.txt";


open(PI, $file) 
    or die "Couldn't open file $file: $!";
    print("file opened\n");
my @data=<PI>;
print("file read\n");
close(PI);
chomp(@data);


my $dbh = connect_to_DB('mysql','interactions','localhost','3306','','pintweb','pintpass');
print("database connected\n");
for my $line(1..10){
##data){
    #print("$data[$line]\n");
    
    my @array = split (/\t|\s+/, $data[$line]);

    #print " pi terms\n@array\n";
    insert_pi_terms($data[$line]);
    if($line%3==0){
    	print ("Inserted line $line\n");
    }
    
}

close(PI);
print("File closed\n");

disconnect_from_DB();
print ("DB disconnected");

sub connect_to_DB {

    my ($driver, $instance, $host, $port, $cnf_file, $user, $password) = @_;

    my $dbh = DBI->connect("DBI:${driver}:database=${instance};host=${host};port=$port;mysql_read_default_file=${cnf_file}",$user,$password)
        or die "ERROR: $DBI::errstr\n";

    if (!defined $dbh) {
        die "Could not connect to database: $!";
    }

    return $dbh;
}


sub disconnect_from_DB {

    $dbh->disconnect()
        or die "Can't disconnect: $DBI::errstr\n";

}


sub insert_pi_terms {

    my $line = shift;

    my @array = split (/\t|\s+/, $line);

   # print "Inside insert pi terms\n@array\n";

    my $insert = qq(INSERT INTO proteins (id,
    					  protein1,
    					  protein2,
                                          score1,
                                          score2)
                    VALUES (?,?,?,?,?)
                   );
    my $sth = $dbh->prepare($insert)
        or die "Can't prepare: $DBI::errstr\n";

    $array[1] = '-'
        if not $array[1];

    $array[6] = '-'
        if not $array[6];

    $sth->execute($array[0],
                  $array[1],
                  $array[2],
                  $array[3],
                  $array[4]);
        #or warn "Can't execute: $DBI::errstr\n";

}
