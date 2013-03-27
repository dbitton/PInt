#!/usr/local/bin/perl  

#
# Author: vp
# Maintainer: 
# Created: 6 december 2010
# Last Modified: 
#many things might be unneccessary, copy pasted code from GLA and YOGI
#Basically there are 2 options: 
#1) find all interactions of one or more proteins with all other proteins
#2) Find interactions only involving a specific list of proteins
# The table highlights whether the predictions match existing known interactions (pombe physical/genetic or cerevisiae physical/genetic)

#Required functionality:
#Ideally represent network of interactions above specified cutoff (there are two SVM and RF), with possibility to expand 
#Ideally no need to open the network on another window
#Colour links according to colour of table field for different type of interactions
#Name nodes with common names where they exist

use strict;

use lib qw(/var/www/lib/core);
use SangerWeb;

use CGI qw/:cgi :standard/;
use CGI::Carp qw(fatalsToBrowser);
use File::Basename;
#use Data::Dumper;

use DBI;

use GD;
use GD::Graph::bars;
use GD::Graph::colour qw(:colours);

use Website::Utilities::IdGenerator;

#$ENV{PATH} = '';
# TODO: many of these hashes should really be put into a database!
local $| = 1;
main();
1;

###############################################################################

sub main {

    my $title = qq(PP: Pombe Protein Interaction Prediction);
    my $cgi   = CGI->new();
    my $sw    = SangerWeb->new({title => $title});

  #  print $sw->header();

    
#<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">


 print qq(Content-type: text/html\n\n);

print qq (<html xmlns="http://www.w3.org/1999/xhtml">
<head>
<meta http-equiv="content-type" content="text/html; charset=utf-8" />
<title>Bahler Lab</title>
<meta name="keywords" content="" />
<meta name="description" content="" />
<link href="/css/other.css" rel="stylesheet" type="text/css" />
</head>
<body>
<div id="header">
<div style="text-align:left; margin-left:70px; margin-bottom:0px; margin-top:0px;"><span style="text-shadow:#FFF; font-family:'Arial Black', Gadget, sans-serif; font-size:32pt; color:#EBF1DE; ">b&auml;hler</span><span style="text-shadow:auto; font-family:'Arial Black', Gadget, sans-serif; font-size:32pt; color:#77933C; ">lab&#13;</span></div>
  <div style="text-align:left; margin-left:30px; margin-top:0px;"><span style="font-family:'Arial Black', Gadget, sans-serif; font-size:20pt; color:#4F6228; "> Genome Regulation</span></div>
  <div class="O">
  <div style="text-align:center; margin-bottom:0px;margin-top:-67px;  margin-left:120px;"><span style="font-family:Arial, Helvetica, sans-serif; font-size:80pt; color:#D7E4BD; "><strong><em>PInt&#13;</em></strong></span></div>
<div style="text-align:right; margin-bottom:0px; margin-top:-129px; margin-left:150px;"><span style="font-family:'Arial Black', Helvetica, sans-serif; font-size:36pt; color:white; ">
<img src="/images/uclogo.gif";/></span></div>
  <div></div>

</div>



</div>
<div id="sidebar">
                <div id="menu">
                        <ul>
                                <li ><a href="/index.html" title="">Home</a></li>
                                <li><a href="/group" title="">People</a></li>
                                <li><a href="/research.htm" title="">Research</a></li>
                                <li><a href="/publications" title="">Publications</a></li>
                                <li class="active first"><a href="/resources" title="">Resources</a></li>

                                <li ><a href="/cont.htm" title="">Contact</a></li>
                        </ul>
                </div>


        </div><div id="content">

                <div class="feature bg7">
        </div>

                        <div class="content" >

);

print qq(<p><img src="/PInt/logoPint.jpg" alt="Logo" width="20%" height="20%" align="right"></p></br></p>);




print start_html("protint");

#eval{
#scriptpart(
    if ($cgi->param() ) {

	
	my $defaultval="OFF";


	my $type=$cgi->param('interactions_type'); ##can be 'amongst' or 'all'
	my $method=$cgi->param('method'); ##can be 'RF and SVM' 'RF' 'SVM'
	
	my $mscore=$cgi->param('minscore'); ##number from 0 to 1
	my $intnum=$cgi->param('intnumber'); ## number of top hits to be returned
	#if ((!defined $mscore or $mscore eq '' )){	 $mscore=0.5; $intnum=100;}
#print "mscore not defined hence $mscore";
	
	#if($intnum>100){$intnum=100;}
#	print "$intnum intnum\n";
	if ($intnum eq '' ){	
	 $intnum=100;
#	print "intnum not defined hence $intnum";
	}
	if ($mscore eq '' ){	
	 $mscore=0.5;
#	print "intnum not defined hence $intnum";
	}
	$defaultval=~/OFF/;
	if($intnum eq '' and $mscore eq ''){
	 $mscore=0.5;
	 $intnum=200;
	$defaultval="ON";
	#print "intnum not defined hence $intnum, $mscore, $defaultval";
	}



	my @gene_info;
	
	my $dbh=connect_to_DB('mysql', 'interactions', 'localhost', '3306', '', 'pintweb', 'pintpass' );
	#my Connecting to interactions database with user pintweb and password pintpass using table pred

	#test_query($dbh);


	my $pre_genelist=undef;
	my $gene=undef;
	my $filename=undef;



        $pre_genelist = $cgi->param('gene_names');
	$gene=$cgi->param('gene');
	#print "url param $gene";
	$filename=$cgi->param('filename');

		#print "$pre_genelist pre genelist or $gene or $filename at line 146";
	#check inputs:
	my $list=0;
	my $g=0;
	my $file=0;
	if($pre_genelist ne ''){$list=1; }
	if($gene ne ''){$g=1; }
	if($filename ne ''){$file=1; }
	my $sum=$list+$g+$file;

	
	#print " $list, $g, $filename, sum $sum</p>\n";
	if($sum>1){
		print qq(You have chosen more than one source for your list please go back<p>);
		print qq(<FORM><INPUT TYPE="button" VALUE="Back" onClick="history.go(-1);return true;" </FORM>);
		exit;
	}
	if($pre_genelist eq ''){
	#print "pregenelist = $pre_genelist hence need gene $gene";
	$pre_genelist = $gene;
	
	}
	

	if($pre_genelist eq '' and $filename ne '' ){
		
		$pre_genelist=upload($cgi);
		
	}
	#print "pre genelist at 173 $pre_genelist<p>\n ";
	
    	my @genelist = split(/\s+|\t|\n|\|,|,\s+/,($pre_genelist));
	#print "@genelist genelist at 173<p>\n ";

##################################
##Retrieve all entries from variours hashes

	my (%common)=ID2name();
	my (%ids)=name2ID();

	my (%product)=getdesc();

	my (%protcer)=getcerprotint();


	my (%protpb)=getpbprotint();
	
	
	my (%genpb)=getpbgen();


	my (%gencer)=getcergen();

	my %nodes;
	my %edges;

#####################################
        my (@proc_genelist)=check_genenames(\@genelist, \%common,\%ids);

	
	  @genelist=@proc_genelist;

	#print "genelist here at line 184@genelist<p>\n";

	#print "cbf11: $product{$genelist[0]}\n";


#my @keys=keys%product;
#print "keys at prod @keys<p>\n";
#print"hash test: $common{$genelist[0]}    random test $keys[2]\t $common{$keys[2]}<p>\n";
#my @keys2=keys%ids;
#print"hash test: $keys2[1]\t$ids{$keys2[1]}<p>\n";
#my @keys2=keys%product;
#print"hash test: $product{$genelist[0]}random test $keys2[2]\t $product{$keys2[2]}<p>\n";
#print "\n<p> NOTE: THE WEBSITE IS UNDERGOING MAINTENANCE, some functions might be not working correctly<p>\n";
if(! defined @genelist or $genelist[0]=~/^$/){
         	 print qq(<p> You haven't chosen any proteins, please go back<p>); 
#			 <a href="/PInt/protint_index.htm">go back</a> <p>);
	}
else{

	  $pre_genelist='';
	  for my $i(0..$#genelist-1){
		$pre_genelist.="$genelist[$i] ";
 }
  $pre_genelist.=$genelist[$#genelist];

		#print "Pre_genelist in main program: $pre_genelist";
  my $singleprot='notsingle';###flag for single protein
		my $countlist=$#genelist+1;
  if($#genelist==0){
		 $singleprot=$genelist[0];
		
	print "<p>You are looking for interactions of protein:<p>\n @genelist=$common{$genelist[0]}\n";
  }
  if($#genelist>0){
		if($type=~/amongst/){
			print "<p>You are looking for interactions amongst $countlist proteins:<p>\n <b>@genelist<p> </b>(common names:<b>";
		}
		if($type=~/all/){
			print "<p>You are looking for all interactions of $countlist proteins:<p>\n <b> @genelist<p><p> </b>(common names:<b>";
		}
		for my $i(0..$#genelist-1){
			print " $common{$genelist[$i]},";
		}
		print " $common{$genelist[$#genelist]}</b>)<p>";
		}
		#print "later default val $defaultval";
		if($defaultval=~/ON/){
			print "<p>You didn't specify a threshold or maximum number of hits. Shown are the first <b>100</b> hits predicted with <b>$method </b> with score above <b>0.5</b>.<p>\n";  
		}
		if($intnum<5000 and $defaultval!~/ON/){
		  print "<p>Predicted with <b> $method </b>above score <b> $mscore </b>and showing a maximum of <b>$intnum</b> hits.<p>\n";
		  }
		#  if($intnum==5000 and $defaultval=="OFF"){
	  	#  print "<p>All interactions predicted with $method with score above $mscore.<p>\n";
		#  }

	print qq(<p><a href="#table">View results in a table</a> &nbsp;&nbsp;&nbsp;&nbsp;                 <a href="#download">Download predictions</a>);
# <a href="http://www.bahlerlab.info/PInt">Reset search</a>);
	print qq(<p><FORM METHOD="LINK" ACTION="a href="http://www.bahlerlab.info/PInt"> <INPUT TYPE="submit" VALUE="Reset search"></FORM>);
#####makes table appear after the network
print qq(
    
   
 <div id="table_div" style="position: relative; padding-top: 1000 ">);	


###########################print colour legend:
	print qq(<p><a name="table">Known interactions are highlighted as follows:<p>\n);
          print qq(<table border='1' ><tr>
			<th bgcolor="#99FF99">Protein interaction in fission yeast</th>
			<th bgcolor="#CCFFFF">Genetic interaction in fission yeast</th>
			<th bgcolor="#FFF99">Protein interaction in budding yeast</th>
			<th bgcolor="#FFCCCC">Genetic interaction in budding yeast</th>
			</tr></table><br>);

	  my $sth_query=get_interactions($dbh, $pre_genelist, $type, $method, $mscore, $intnum, $singleprot);


  
	  if($singleprot=~/notsingle/){
		my $count =print_results_table($sth_query, $method, $mscore, $intnum, $pre_genelist, \%common, \%product, \%protcer, \%protpb, \%genpb, \%gencer);
		#print "\n\n<p>using multiple protein results format<p>\n";
	  }
	  else{
	   my $count=print_results_single_table($sth_query, $method, $mscore, $intnum, $pre_genelist, \%common, \%product, \%protcer, \%protpb, \%genpb, \%gencer);
		#print "\n\n<p>using single protein results protcer=<p>\n";
		
	  }
print qq(</div>);
          disconnect_from_DB($dbh);
	  #print "disconnected<p>\n";


	}
 }##end cgi param

#);###end scriptpart 
#1;
#}
#or do{ print "There was an error with the processing, contact the website administrator";
#};

	print end_html;
	
  
	print qq(<FORM><INPUT TYPE="button" VALUE="Back" onClick="history.go(-1);return true;" </FORM>);

}    
#############
sub upload{

my ($cgi)=@_;

my $filename = $cgi->param('filename');  

#print "Inside upload file subroutine<p>\n$filename<p>\n";
 
if ( !$filename )  
{  
 #print $cgi->header ( );  
 print "There was a problem uploading your file $filename (try a smaller file).";  
 exit;  
}  
   
my ( $name, $path, $extension ) = fileparse ( $filename, '\..*' );  
$filename = $name . $extension;  
$filename =~ tr/ /_/;  

my $safe_filename_characters = "a-zA-Z0-9_.-"; 
$filename =~ s/[^$safe_filename_characters]//g;  
 
if ( $filename =~ /^([$safe_filename_characters]+)$/ )  
{  
 $filename = $1;  
}  
else  
{  
 die "Filename contains invalid characters";  
}  

 
my $filename = $cgi->upload('filename');  

my @time=localtime;
my $output_file= "/var/www/htdocs/PInt/tmp/uploaded".$time[0].$time[1].$time[2].".txt";
open ( OUTPUTFILE, ">","$output_file" ) or die "Couldn't open $output_file for writing: $!";  
#print "File opened!!!!<p>\n";
 my ($bytesread, $buffer);
    my $numbytes = 1024;

my $text='';
while($bytesread=read($filename, $buffer, $numbytes)){
	print OUTPUTFILE $buffer;
	$text=$text.$buffer;
} 

close OUTPUTFILE;

##check that text only contains correc characters and separators:
if($text!~/^[a-zA-Z0-9.\s]/){
 $text='';	
 print"<p>There is a problem with your file $filename, it contains illegal characters<p>";
}
if($text!~/^$/){
print"<p>Thanks for uploading your file $filename</p> ";
}

#print "<p>$text<p>\n" ;
    
return($text);
}
###############################################################################
sub get_interactions{   ###choose different queries depending on parameter choices

	my($dbh, $pre_genelist, $type, $method, $mscore, $intnum, $singleprot)=@_;
	
	#print "Inside get_interactions singleprot:$singleprot, pregenelist: $pre_genelist\n";
	my %gene_interactions=undef;

	my $sth_query=undef;

	if($type eq 'all' or $singleprot!~/notsingle/){
		$sth_query=get_all_interactions($dbh, $pre_genelist, $method, $mscore, $intnum);
		#print " inside get all ints<p>\n";

		
	}
	if($type eq 'amongst' and $singleprot=~/notsingle/){
	        $sth_query=get_amongst_interactions($dbh, $pre_genelist, $method, $mscore, $intnum);
		#print "inside amongst<p>\n"
	}
	return($sth_query);

}     
##############################################################################
sub get_all_interactions {

    my ($dbh, $pre_genelist, $method, $mscore, $intnum) = @_;

	my $sth_query=undef;

    my @genelist= split(/\s+/,$pre_genelist); 
  #print "@genelist\n  <p>Method $method inside all interactions<p>\n score=$mscore<p>\n";
	
    
	my $whichscore;
	my $RFminscore;
 
 #   print "Method $method inside all interactions<p>\n";
	if($method eq 'SVM'){
		$whichscore='scoreSVM';
		$RFminscore=0;
		
    }
	
    if( $method eq 'RF'){ 
		$whichscore='scoreRF';
		$RFminscore=$mscore;
    }
    if( $method eq 'RF and SVM'){ 
        $whichscore='scoreSVM';
		$RFminscore=0.5;
    }
   my $post_genelist=$pre_genelist;
    $post_genelist=~s/\s+|\t/','/g;
    $post_genelist="('".$post_genelist."')";

	#print "post=$post_genelist\n";
	#print "pre_genelist=$pre_genelist";

###make a string with a proper array
    
    my $string = qq(SELECT * FROM   pred
		WHERE (protein2 IN $post_genelist
		OR protein1 IN $post_genelist)
		AND $whichscore > $mscore
		AND scoreRF > $RFminscore
		ORDER BY $whichscore DESC);

     $sth_query = $dbh->prepare($string);
#print "$string<p>\n";
return($sth_query);
}

##############################################################################
##get amongst
#######################################
sub get_amongst_interactions {

    my ($dbh, $pre_genelist, $method, $mscore, $intnum) = @_;

	my $sth_query=undef;

    my @genelist= split(/\s+/,$pre_genelist); 
 
	my $whichscore;
	my $RFminscore;
 
 #   print "Method $method inside amongst interactions<p>\n";
	if($method eq 'SVM'){
		$whichscore='scoreSVM';
		$RFminscore=0;
		
    }
	
    if( $method eq 'RF'){ 
		$whichscore='scoreRF';
		$RFminscore=$mscore;
    }
    if( $method eq 'RF and SVM'){ 
        $whichscore='scoreSVM';
		$RFminscore=0.5;
    }


   my $post_genelist=$pre_genelist;
    $post_genelist=~s/\s+|\t/','/g;
    $post_genelist="('".$post_genelist."')";

#print "post=$post_genelist\n";

###make a string with a proper array
    
    my $string = qq(SELECT * FROM   pred
		WHERE protein2 IN $post_genelist
		AND protein1 IN $post_genelist 
		AND $whichscore > $mscore
		AND scoreRF > $RFminscore
		ORDER BY $whichscore DESC);

     $sth_query = $dbh->prepare($string);
#print "$string\n";
	return($sth_query);
}
################


#########################################################print results
sub print_results_table{

my ($sth_query, $method, $mscore, $intnum, $pre_genelist,$common, $product, $protcer, $protpb, $genpb, $gencer)=@_;

(my %common)=%$common;


(my %product)=%$product;


(my %protcer)=%$protcer;


(my %protpb)=%$protpb;


(my %genpb)=%$genpb;


(my %gencer)=%$gencer;

$sth_query->execute();




my @test=$sth_query->fetchrow();
#print "@test<p>\n";
if (! defined @test){
print "There are no predicted interactions.<p>\n";
}
else{
my $count=1;


#print "Test $pre_genelist\t $test[1]\tcomm $common{$test[1]}\t prod $product{$test[1]}<p>\n";
#print"$method<p>\n";

print "<table border='1' ><tr>
<th>Rank</th>
<th>protein 1</th>
<th>protein 2</th>
<th>common name 1</th>
<th>common name 2</th>
<th>product 1</th>
<th>product 2</th>";
if($method eq 'SVM' ){
print"<th>SVM score</th></tr>";
}
if($method eq 'RF'){
print"<th>RF score</th></tr>";
}
if($method eq 'RF and SVM'){
print"<th>SVM score</th><th>RF score</th></tr>";
}

####try accessing file in tmp directory
#my $fin="/var/www/htdocs/PInt/tmp/try.txt";
#open(INFILE, "$fin") or die();
#my @filein=<INFILE>;
#print ("File @filein\n");

##try writing file to the directory
#my $fouttry="/var/www/htdocs/PInt/tmp/tryout.txt";
#open(OUTFILE ,">$fouttry") or die();
#print (OUTFILE "The test now writes to the file\n");
#close(OUTFILE);

##start hash
my %nodes;
my %edges;

###set output files:
#prepare text file name
    my @time=localtime;
   # my $fout="/var/www/PInt/tmp/interactions".$time[0].$time[1].$time[2].$time[3].$time[4].$time[5].".txt";
   # my $foutname="/var/www/PInt/tmp/interactions_onlyname".$time[0].$time[1].$time[2].$time[3].$time[4].$time[5].".txt";

  my $fout="/var/www/htdocs/PInt/tmp/interactions".$time[0].$time[1].$time[2].".txt";
 my $fouthash="/var/www/htdocs/PInt/tmp/hash".$time[0].$time[1].$time[2].".txt";
 
    my $foutname="/var/www/htdocs/PInt/tmp/interactions_onlyname".$time[0].$time[1].$time[2].".txt";


      open(OUTFILE , ">$fout") or die("Cannot open $fout");
    print (OUTFILE "##Interactions predicted with score above $mscore\n");
    print (OUTFILE "##ID1\tID2\tcommon_name1\tcommon_name2\tproduct1\tproduct2\tRFscore\tSVMscore\n");


    open(OUTFILEname , ">$foutname") or die("Cannot open $foutname");
    print (OUTFILEname "##Interactions predicted with score above $mscore\n");
    print (OUTFILEname "##common_name1\tcommon_name2\tRFscore\tSVMscore\n");


###############print data from the test: very inelegant but if not like this the first prediction is always lost...
## could write a count query separate from the retrieval one.

####for text file:
	$nodes{"$common{$test[1]}"}=1;
	$nodes{"$common{$test[2]}"}=1;
	if($pre_genelist=~/$test[2]/i and $pre_genelist!~/$test[1]/i){
		print (OUTFILE "$test[2]\t$test[1]\t$common{$test[2]}\t$common{$test[1]}\t$product{$test[2]}\t$product{$test[1]}\t$test[3]\t$test[4]\t\n");

		print (OUTFILEname "$common{$test[2]}\t$common{$test[1]}\t$test[3]\t$test[4]\n");
	}
	if($pre_genelist=~/$test[1]/i  ){
		print (OUTFILE "$test[1]\t$test[2]\t$common{$test[1]}\t$common{$test[2]}\t$product{$test[1]}\t$product{$test[2]}\t$test[3]\t$test[4]\n");
		print (OUTFILEname "$common{$test[1]}\t$common{$test[2]}\t$test[3]\t$test[4]\n");

	$nodes{"$common{$test[1]}"}="query";
        }
	if($pre_genelist=~/$test[2]/i){ 	
	$nodes{"$common{$test[2]}"}="query";
	}

	#$edges{"$common{$test[1]}TO$common{$test[2]}"}=($test[3]+$test[4])/2;

	#$edges{"$common{$test[2]}TO$common{$test[1]}"}=1;

#### end text file print

#print "<p>Proteins here are $test[1] and $test[2]<p>\n";

#if(defined $protpb}{"$test[1],$test[2]"}){
	#print ("Seen inside database\n<p>");
#}
#print qq(a$test[1]and$test[2]a<p>\n);


#my @keysprot=keys%protpb;
#print "<p>$keysprot[0]<p>\n";

#print "<p>$keysprot[1]<p>\n";

#print "<p>$keysprot[2]<p>\n";
#print "keys inside results table are $#keysprot<p>\n";
#for my $i(0..$#keysprot){
#if($keysprot[$i]=~/"SPAC19D5.01"/){
#print  "LKeys of protpb: $keysprot[1],$protpb{$keysprot[1]}<p>\n";
#}
#}

#if(($test[1]=~/SPAC19D5.01/ && $test[2]=~/SPAC24B11.06C/) ||($test[2]=~/SPAC19D5.01/ && $test[1]=~/SPAC24B11.06C/) ){
#			print "<p>pyp2 and sty1 found in databases withint print !!!\n";
#		}
	my $color="#FFFFFF";
	my $int="";
	
	if(defined $gencer{"$test[1],$test[2]"}){
		$color="#FFCCCC";
		$int="gencer";
		
	}
	if(defined $protcer{"$test[1],$test[2]"}){
		 $color="#FFFF99";
		$int="protcer";
	}
	if(defined $genpb{"$test[1],$test[2]"}){
		$color="#CCFFFF";
		$int="genpb";
	}
	if(defined $protpb{"$test[1],$test[2]"}){
		$color="#99FF99";
		$int="protpb";
		#print "Found pombe ints!!!!!!!!!!!!!!<p>\n";
	}

	

	if($count<=$intnum){
          print qq(<tr bgcolor=$color>
	  <td>).$count."</td>";


	if($pre_genelist =~/$test[2]/i and $pre_genelist!~/$test[1]/){
		 print "<td>".$test[2]."</td>
	         <td>".$test[1]."</td>
		 <td>".$common{$test[2]}."</td>
	         <td>".$common{$test[1]}."</td>
		 <td>".$product{$test[2]}."</td>
	         <td>".$product{$test[1]}."</td>";
	}
	if($pre_genelist=~/$test[1]/i ){
		 print "<td>".$test[1]."</td>
	         <td>".$test[2]."</td>
		 <td>".$common{$test[1]}."</td>
	         <td>".$common{$test[2]}."</td>
		 <td>".$product{$test[1]}."</td>
	         <td>".$product{$test[2]}."</td>";
	}
	if($method eq 'SVM' ){
	    print"<td>".$test[4]."</td></tr>";
$edges{"$common{$test[1]}TO$common{$test[2]}INT$int"}=$test[4];

	}
	if($method eq 'RF'){
	   print"<td>".$test[3]."</td></tr>";
$edges{"$common{$test[1]}TO$common{$test[2]}INT$int"}=$test[3];

	}
	if($method eq 'RF and SVM'){
	   print"<td>".$test[4]."</td><td>".$test[3]."</td></tr>";
$edges{"$common{$test[1]}TO$common{$test[2]}INT$int"}=($test[3]+$test[4])/2;

	}


       }
       $count=$count+1;

 ################now retrieve data in loop
   while( my  @row = $sth_query->fetchrow()){

####for text file:
	if($pre_genelist=~/$row[2]/i and $pre_genelist!~/$row[1]/i){
		print (OUTFILE "$row[2]\t$row[1]\t$common{$row[2]}\t$common{$row[1]}\t$product{$row[2]}\t$product{$row[1]}\t$row[3]\t$row[4]\t\n");

		print (OUTFILEname "$common{$row[2]}\t$common{$row[1]}\t$row[3]\t$row[4]\n");
	}
	if($pre_genelist=~/$row[1]/i  ){
		print (OUTFILE "$row[1]\t$row[2]\t$common{$row[1]}\t$common{$row[2]}\t$product{$row[1]}\t$product{$row[2]}\t$row[3]\t$row[4]\n");
		print (OUTFILEname "$common{$row[1]}\t$common{$row[2]}\t$row[3]\t$row[4]\n");
        }
#	$nodes{"$common{$row[1]}"}=1;
#	$nodes{"$common{$row[2]}"}=1;
#	$edges{"$common{$row[1]}TO$common{$row[2]}"}=1;

	#$edges{"$common{$row[2]}TO$common{$row[1]}"}=1;
#### end text file print

#print "Proteins here are $test[1] and $test[2]<p>\n";
#if(($test[1]=~/SPAC19D5.01/ && $test[2]=~/SPAC24B11.06C/) ||($test[2]=~/SPAC19D5.01/ && $test[1]=~/SPAC24B11.06C/) ){
#			print "<p>pyp2 and sty1 found in databases withint print !!!\n";
#		}
	 my $color="#FFFFFF";
	my $int="";
	if(defined $gencer{"$row[1],$row[2]"}){
		$color="#FFCCCC";
		$int="gencer";
		#print "Found pombe ints!!!!!!!!!!!!!!<p>\n";
		
	}

	if(defined $protcer{"$row[1],$row[2]"}){
		 $color="#FFFF99";
		$int="protcer";
	}
	if(defined $genpb{"$row[1],$row[2]"}){
		$color="#CCFFFF";
		$int="genpb";
	}
	if(defined $protpb{"$row[1],$row[2]"}){
		$color="#99FF99";
		$int="protpb";
		#print "Found pombe ints!!!!!!!!!!!!!!<p>\n";
	}
	


	if($count<=$intnum){

	$nodes{"$common{$row[1]}"}=1;
	$nodes{"$common{$row[2]}"}=1;
	
	#$edges{"$common{$test[1]}TO$common{$test[2]}"}.="INT$int";


	#$edges{"$common{$row[2]}TO$common{$row[1]}"}=1;
          print qq(<tr bgcolor=$color>
	  <td>).$count."</td>";

	if($pre_genelist =~/$row[2]/i and $pre_genelist!~/$row[1]/){
		 print "<td>".$row[2]."</td>
	         <td>".$row[1]."</td>
		 <td>".$common{$row[2]}."</td>
	         <td>".$common{$row[1]}."</td>
		 <td>".$product{$row[2]}."</td>
	         <td>".$product{$row[1]}."</td>";
	}
	if($pre_genelist=~/$row[1]/i ){
		 print "<td>".$row[1]."</td>
	         <td>".$row[2]."</td>
		 <td>".$common{$row[1]}."</td>
	         <td>".$common{$row[2]}."</td>
		 <td>".$product{$row[1]}."</td>
	         <td>".$product{$row[2]}."</td>";
	$nodes{"$common{$row[1]}"}="query";
	}
if($pre_genelist=~/$row[2]/i ){
	$nodes{"$common{$row[2]}"}="query";
	}

	if($method eq 'SVM' ){
	    print"<td>".$row[4]."</td></tr>";
$edges{"$common{$row[1]}TO$common{$row[2]}INT$int"}=$row[4];
	}
	if($method eq 'RF'){
	   print"<td>".$row[3]."</td></tr>";

$edges{"$common{$row[1]}TO$common{$row[2]}INT$int"}=$row[3];
	}
	if($method eq 'RF and SVM'){
	   print"<td>".$row[4]."</td><td>".$row[3]."</td></tr>";

$edges{"$common{$row[1]}TO$common{$row[2]}INT$int"}=($row[3]+$row[4])/2;
	}


       }##end if
       $count=$count+1;

   }## end while
print("</table>");
close(OUTFILE);
close(OUTFILENAME);

my $fout2=$fout;
$fout2=~s/\/var\/www\/htdocs//g;

my $foutname2=$foutname;

$foutname2=~s/\/var\/www\/htdocs//g;


$count=$count-1;
print "<p>There are a total of $count predictions with $method above $mscore.<p>";
print qq(<p><a name="download"><a href=$fout2>Download</a> all the predictions as a tab separated text file with 
IDs, 
common names and gene ontology definition</p>);
print qq(<p><a href=$foutname2>Download</a> all the predictions as a tab separated text file only with common names</p>);
#print qq(<p>If you want to visualize the predicted interaction network, save the file only with names and open it in the BioLayout viewer:     <a href="http://www.biolayout.org/downloads/BioLayoutExpress3DWebStart.php"><img src="/PInt/webstart-launch-button.png" alt="Start BioLayout Express 3D" width="88" height="23"></a></p>);


my $res_net_data="";

      open(OUTFILE , ">$fouthash") or die("Cannot open $fouthash");
print(OUTFILE "nodes: [");
$res_net_data.="nodes: [";

my @ke=keys%nodes;
for my $key(0..$#ke-1){

print (OUTFILE "{id: \"$ke[$key]\", label: \"$ke[$key]\", query: \"$nodes{$ke[$key]}\"},");
$res_net_data.="{id: \"$ke[$key]\", label: \"$ke[$key]\", query: \"$nodes{$ke[$key]}\"},";
}
print(OUTFILE "{id: \"$ke[$#ke]\",label: \"$ke[$#ke]\", query: \"$nodes{$ke[$#ke]}\"}],\nedges: [");
$res_net_data.="{id: \"$ke[$#ke]\",label: \"$ke[$#ke]\", query: \"$nodes{$ke[$#ke]}\"}],\nedges: [";

@ke=keys%edges;
for my $key(0..$#ke-1){    
(my $tar,my $sour, my $int )=split(/TO|INT/,$ke[$key]);
print (OUTFILE "{id: \"$tar TO$sour\", target: \"$tar\", source: \"$sour\", weight: $edges{$ke[$key]} , type: \"$int\"},");
$res_net_data.="{id: \"$tar TO$sour\", target: \"$tar\", source: \"$sour\", weight: $edges{$ke[$key]}, type: \"$int\"},";
}

(my $tar,my $sour, my $int )=split(/TO|INT/,$ke[$#ke]);
print(OUTFILE "{id: \"$tar TO$sour\", target: \"$tar\", source: \"$sour\", weight: $edges{$ke[$#ke]}, type: \"$int\"}]");
$res_net_data.="{id: \"$tar TO$sour\", target: \"$tar\", source: \"$sour\", weight: $edges{$ke[$#ke]}, type: \"$int\"}]";
 
my $cyto=loadcytoweb($res_net_data);
return($res_net_data);
}### successful prediction

}

###############################################################print results for single protein
sub print_results_single_table{

my ($sth_query, $method, $mscore, $intnum, $pre_genelist,$common, $product, $protcer, $protpb, $genpb, $gencer)=@_;

(my %common)=%$common;


(my %product)=%$product;


(my %protcer)=%$protcer;


(my %protpb)=%$protpb;


(my %genpb)=%$genpb;


(my %gencer)=%$gencer;


$sth_query->execute();

my %nodes;
my %edges;


my @test=$sth_query->fetchrow();
#print "@test<p>\n";
if (! defined @test){
print "There are no predicted interactions.<p>\n";
}
else{
my $count=1;


#print "Test $pre_genelist\t $test[1]\tcomm $common{$test[1]}\t prod $product{$test[1]}<p>\n";
#print"$method<p>\n";

print "<table border='1' ><tr>
<th>Rank</th>
<th>protein</th>

<th>common name</th>

<th>product</th>";

if($method eq 'SVM' ){
print"<th>SVM score</th></tr>";
}
if($method eq 'RF'){
print"<th>RF score</th></tr>";
}
if($method eq 'RF and SVM'){
print"<th>SVM score</th><th>RF score</th></tr>";
}


###set output files:
#prepare text file name
    my @time=localtime;
   my $fout="/var/www/htdocs/PInt/tmp/interactions".$time[0].$time[1].$time[2]."txt";

   my $fouthash="/var/www/htdocs/PInt/tmp/hash".$time[0].$time[1].$time[2]."txt";

    my $foutname="/var/www/htdocs/PInt/tmp/interactions_onlyname".$time[0].$time[1].$time[2]."txt";

      open(OUTFILE , ">$fout") or die("Cannot open $fout");
    print (OUTFILE "##Interactions predicted with score above $mscore\n");
    print (OUTFILE "##ID1\tID2\tcommon_name1\tcommon_name2\tproduct1\tproduct2\tRFscore\tSVMscore\n");


    open(OUTFILEname , ">$foutname") or die("Cannot open $foutname");
    print (OUTFILEname "##Interactions predicted with score above $mscore\n");
    print (OUTFILEname "##common_name1\tcommon_name2\tRFscore\tSVMscore\n");


###############print data from the test: very inelegant but if not like this the first prediction is always lost...
## could write a count query separate from the retrieval one.

####for text file:
	$nodes{"$common{$test[1]}"}=1;
	$nodes{"$common{$test[2]}"}=1;
	if($pre_genelist=~/$test[2]/i and $pre_genelist!~/$test[1]/i){
		print (OUTFILE "$test[2]\t$test[1]\t$common{$test[2]}\t$common{$test[1]}\t$product{$test[2]}\t$product{$test[1]}\t$test[3]\t$test[4]\t\n");

		print (OUTFILEname "$common{$test[2]}\t$common{$test[1]}\t$test[3]\t$test[4]\n");
	}
	if($pre_genelist=~/$test[1]/i  ){
		print (OUTFILE "$test[1]\t$test[2]\t$common{$test[1]}\t$common{$test[2]}\t$product{$test[1]}\t$product{$test[2]}\t$test[3]\t$test[4]\n");
		print (OUTFILEname "$common{$test[1]}\t$common{$test[2]}\t$test[3]\t$test[4]\n");

	$nodes{"$common{$test[1]}"}="query";
        }
if($pre_genelist=~/$test[2]/i  ){
	$nodes{"$common{$test[2]}"}="query";
        }

	#$edges{"$common{$test[1]}TO$common{$test[2]}INT$int"}=($test[3]+$test[4])/2;

#### end text file print



#print "Proteins here are $test[1] and $test[2]<p>\n";
#if(($test[1]=~/SPAC19D5.01/ && $test[2]=~/SPAC24B11.06C/) ||($test[2]=~/SPAC19D5.01/ && $test[1]=~/SPAC24B11.06C/) ){
#			print "<p>pyp2 and sty1 found in databases withint print !!!\n";
#		}



###select color of row:
	my $color="#FFFFFF";
	my $int="";
	
	if(defined $gencer{"$test[1],$test[2]"}){
		$color="#FFCCCC";
		$int="gencer";
		
	}
	if(defined $protcer{"$test[1],$test[2]"}){
		 $color="#FFFF99";
		$int="protcer";
	}
	if(defined $genpb{"$test[1],$test[2]"}){
		$color="#CCFFFF";
		$int="genpb";
	}
	if(defined $protpb{"$test[1],$test[2]"}){
		$color="#99FF99";
		$int="protpb";
		#print "Found pombe ints!!!!!!!!!!!!!!<p>\n";
	}

	

	


	if($count<=$intnum){
          print qq(<tr bgcolor=$color>
	  <td>).$count."</td>";

	if($pre_genelist =~/$test[2]/i and $pre_genelist!~/$test[1]/){
		 print "<td>".$test[1]."</td>
	         <td>".$common{$test[1]}."</td>
	         
		 <td>".$product{$test[1]}."</td>";

	}
	if($pre_genelist=~/$test[1]/i ){
		 print "<td>".$test[2]."</td>

		 <td>".$common{$test[2]}."</td>

		 <td>".$product{$test[2]}."</td>";

	}
	if($method eq 'SVM' ){
	    print"<td>".$test[4]."</td></tr>";
$edges{"$common{$test[1]}TO$common{$test[2]}INT$int"}=$test[4];

	}
	if($method eq 'RF'){
	   print"<td>".$test[3]."</td></tr>";
$edges{"$common{$test[1]}TO$common{$test[2]}INT$int"}=$test[3];

	}
	if($method eq 'RF and SVM'){
	   print"<td>".$test[4]."</td><td>".$test[3]."</td></tr>";
$edges{"$common{$test[1]}TO$common{$test[2]}INT$int"}=($test[3]+$test[4])/2;

	}


       }
       $count=$count+1;

 ################now retrieve data in loop
   while( my  @row = $sth_query->fetchrow()){

####for text file:
	if($pre_genelist=~/$row[2]/i and $pre_genelist!~/$row[1]/i){
		print (OUTFILE "$row[2]\t$row[1]\t$common{$row[2]}\t$common{$row[1]}\t$product{$row[2]}\t$product{$row[1]}\t$row[3]\t$row[4]\t\n");

		print (OUTFILEname "$common{$row[2]}\t$common{$row[1]}\t$row[3]\t$row[4]\n");
	}
	if($pre_genelist=~/$row[1]/i  ){
		print (OUTFILE "$row[1]\t$row[2]\t$common{$row[1]}\t$common{$row[2]}\t$product{$row[1]}\t$product{$row[2]}\t$row[3]\t$row[4]\n");
		print (OUTFILEname "$common{$row[1]}\t$common{$row[2]}\t$row[3]\t$row[4]\n");
        }
#	$nodes{"$common{$row[1]}"}=1;
#	$nodes{"$common{$row[2]}"}=1;
#	$edges{"$common{$row[1]}TO$common{$row[2]}"}=1;

	#$edges{"$common{$row[2]}TO$common{$row[1]}"}=1;
#### end text file print

	 my $color="#FFFFFF";
	my $int="";
	if(defined $gencer{"$row[1],$row[2]"}){
		$color="#FFCCCC";
		$int="gencer";
		#print "Found pombe ints!!!!!!!!!!!!!!<p>\n";
		
	}
	if(defined $protcer{"$row[1],$row[2]"}){
		 $color="#FFFF99";
		$int="protcer";
	}
	if(defined $genpb{"$row[1],$row[2]"}){
		$color="#CCFFFF";
		$int="genpb";
	}
	if(defined $protpb{"$row[1],$row[2]"}){
		$color="#99FF99";
		$int="protpb";
		#print "Found pombe ints!!!!!!!!!!!!!!<p>\n";
	}




	if($count<=$intnum){

	$nodes{"$common{$row[1]}"}=1;
	$nodes{"$common{$row[2]}"}=1;
	#$edges{"$common{$test[1]}TO$common{$test[2]}"}.="INT$int";

	#$edges{"$common{$test[2]}TO$common{$test[1]}"}=1;

          print qq(<tr bgcolor=$color>
	  <td>).$count."</td>";


	if($pre_genelist =~/$row[2]/i and $pre_genelist!~/$row[1]/){
		 print "<td>".$row[1]."</td>

		 <td>".$common{$row[1]}."</td>

		 <td>".$product{$row[1]}."</td>";
	}
	if($pre_genelist=~/$row[1]/i ){
		 print "<td>".$row[2]."</td>

		 <td>".$common{$row[2]}."</td>

		 <td>".$product{$row[2]}."</td>";
	$nodes{"$common{$row[1]}"}="query";
	}
if($pre_genelist=~/$row[2]/i ){
	$nodes{"$common{$row[2]}"}="query";
}
	if($method eq 'SVM' ){
	    print"<td>".$row[4]."</td></tr>";

	$edges{"$common{$row[1]}TO$common{$row[2]}INT$int"}=$row[4];
	}
	if($method eq 'RF'){
	   print"<td>".$row[3]."</td></tr>";

	$edges{"$common{$row[1]}TO$common{$row[2]}INT$int"}=$row[3];
	}
	if($method eq 'RF and SVM'){
	   print"<td>".$row[4]."</td><td>".$row[3]."</td></tr>";

	$edges{"$common{$row[1]}TO$common{$row[2]}INT$int"}=($row[3]+$row[4])/2;
	}


       }##end if
       $count=$count+1;

   }## end while
print("</table>");
close(OUTFILE);
close(OUTFILENAME);
$count=$count-1;

my $fout2=$fout;
$fout2=~s/\/var\/www\/htdocs//g;

my $foutname2=$foutname;
$foutname2=~s/\/var\/www\/htdocs//g;


print "<p>There are a total of $count predictions with $method above $mscore.<p>\n";

print qq(<p><a name="download"><a href=$fout2>Download</a> all the predictions as a tab separated text file with IDs and common names</p>);
print qq(<p><a href=$foutname2>Download</a> all the predictions as a tab separated text file only with common names</p>);
#print qq(<p>If you want to visualize the predicted interaction network, save the file only with names and open it in the BioLayout viewer:     <a href="http://www.biolayout.org/#downloads/BioLayoutExpress3DWebStart.php"><img src="/PInt/webstart-launch-button.png" alt="Start BioLayout Express 3D" width="88" height="23"></a></p>);



my $res_net_data="";

      open(OUTFILE , ">$fouthash") or die("Cannot open $fouthash");
print(OUTFILE "nodes: [");
$res_net_data.="nodes: [";

my @ke=keys%nodes;
for my $key(0..$#ke-1){  
print (OUTFILE "{id: \"$ke[$key]\", label: \"$ke[$key]\", query: \"$nodes{$ke[$key]}\"},");
$res_net_data.="{id: \"$ke[$key]\", label: \"$ke[$key]\", query: \"$nodes{$ke[$key]}\"},";
}
print(OUTFILE "{id: \"$ke[$#ke]\",label: \"$ke[$#ke]\", query: \"$nodes{$ke[$#ke]}\"}],\nedges: [");
$res_net_data.="{id: \"$ke[$#ke]\",label: \"$ke[$#ke]\", query: \"$nodes{$ke[$#ke]}\"}],\nedges: [";

@ke=keys%edges;
for my $key(0..$#ke-1){    
(my $tar,my $sour, my $int )=split(/TO|INT/,$ke[$key]);
print (OUTFILE "{id: \"$tar TO$sour\", target: \"$tar\", source: \"$sour\", weight: $edges{$ke[$key]} , type: \"$int\"},");
$res_net_data.="{id: \"$tar TO$sour\", target: \"$tar\", source: \"$sour\", weight: $edges{$ke[$key]}, type: \"$int\"},";
}

(my $tar,my $sour, my $int )=split(/TO|INT/,$ke[$#ke]);
#print qq(<p>$ke[$#ke]</p>);
print(OUTFILE "{id: \"$tar TO$sour\", target: \"$tar\", source: \"$sour\", weight: $edges{$ke[$#ke]}, type: \"$int\"}]");
$res_net_data.="{id: \"$tar TO$sour\", target: \"$tar\", source: \"$sour\", weight: $edges{$ke[$#ke]}, type: \"$int\"}]";
 
my $cyto=loadcytoweb($res_net_data);
return($res_net_data);
}### successful prediction

}
#################################

sub loadcytoweb{
####to make a box with cytoscapeweb window

my ($res_net_data)=@_;


#print qq(<p> $res_net_data</p>);

#$res_net_data="nodes: [ { id: \"1\" }, { id: \"2\" } ],\nedges: [ { id: \"2to1\", target: \"1\", source: \"2\" } ]";
#my $filein="/tmp/hash561710txt";
#open(INFILE, "$filein") or die();
my $datafile="inside data file\n$res_net_data";

#print qq(<p> $datafile</p>);


#print qq( <p>  Under Construction</p>);



print qq( 

<script type="text/javascript" src="script.js"></script>

<!-- JSON support for IE (needed to use JS API) -->


	
       <script type="text/javascript" src="/PInt/js/min/json2.min.js"></script>
        
        <!-- Flash embedding utility (needed to embed Cytoscape Web) -->
        <script type="text/javascript" src="/PInt/js/min/AC_OETags.min.js"></script>

        
        <!-- Cytoscape Web JS API (needed to reference org.cytoscapeweb.Visualization) -->
        <script type="text/javascript" src="/PInt/js/min/cytoscapeweb.min.js"></script>

	
 <script type="text/javascript">
window.onload=function() {
                // id of Cytoscape Web container div
                var div_id = "cytoscapeweb";
                
                // you could also use other formats (e.g. GraphML) or grab the network data via AJAX

                var networ_json = {
		dataSchema: {
    		nodes: [
    		    { name: "id",    type: "string" },
   		     { name: "label", type: "string" },
			{name: "query", type: "string"}
    		],
		 edges: [ { name: "weight", type: "number" },
			  {name: "type", type: "string"}
                ]
		
		},
                  data: { 

$res_net_data
                 //       nodes: [ { id: "1" }, { id: "2" }, {id: "3"}, {id: "4"} ]
		//	edges: [ { id: "2to1", target: "1", source: "2" }, { id: "3to1", target: "1", source: "3" }]
                //        nodes: [ { id: "atf1", label: "atf1"}, { id: "spt2", label: "spt2" }, {id: "kms1", label:"kms1"}, {id: "swc2", label: "swc2"} ],
		//	edges: [ { id: "spt2toatf1", target: "spt2", source: "atf1", weight: 0.2242423, type: "physical" }, { id: "kms1toatf1", target: "kms1", source: "atf1", weight: 0.9243234, type: "genetic" }]                 
                    }             

                };
                
                // initialization options
                var options = {
                    // where you have the Cytoscape Web SWF
                    swfPath: "/PInt/swf/CytoscapeWeb",
                    // where you have the Flash installer SWF
                    flashInstallerPath: "/PInt/swf/playerProductInstall"
                };
                
                // init and draw
                var vis = new org.cytoscapeweb.Visualization(div_id,options);

		vis.draw({network: networ_json,
        nodeLabelsVisible: true,
	visualStyle: {
          global: {
               backgroundColor: "#ffffff",
               tooltipDelay: 1
          },
 	  nodes: {
		label: { passthroughMapper: { attrName: "label" } },
		labelHorizontalAnchor: "center",
                labelVerticalAnchor: "middle",
                labelFontSize: 24,
		 labelFontWeight: "bold",
                selectionBorderWidth: 2,
                selectionBorderColor: "#000000",
                selectionGlowColor: "#ffff00",
		color: {discreteMapper:{defaultValue: "#FFFF00", attrName: "query",
				entries: [
                                     { attrValue: "query", value: "#FF0000" }
			   ]
		}},
		size: 40
   	  },//end nodes
	edges: {
		color: { discreteMapper: { defaultValue: "#FFFFFF", attrName: "type",
			   entries: [
                                     { attrValue: "protcer", value: "#FFFF00" },
				     { attrValue: "gencer", value: "#FA5858" },
				     { attrValue: "genpb", value: "#0174DF" },
				     { attrValue: "protpb", value: "#2EFE2E" },

			   ]
			 } },
		width: {continuousMapper: {defaultValue: 12, attrName: "weight",

                                         minValue: 3, 
                                         maxValue: 15 } }

	}
	}//end visual style
});
};// end onload
        </script>
        
       
<style type="text/css">
    /* The Cytoscape Web container must have its dimensions set. */
    html, body { height: 100%; width: 100%; padding: 0; margin: 0; }
    /* use absolute value */
    #cytoscapeweb{ width: 1000px; height: 800px;  }

    SPAN.physical
    {
       BACKGROUND-COLOR: #FF0000;
       COLOR: #FF0000;
       FONT-SIZE: 2px;
       padding-top:0px;
       padding-bottom:0px;
       padding-right:18px;
       padding-left:18px;
       position:absolute;
       top:-4px;
    }
    .genetic
    {
       BACKGROUND-COLOR: #6666FF;
       COLOR: #6666FF;
       FONT-SIZE: 2px;
       padding-top:0px;
       padding-bottom:0px;
       padding-right:18px;
       padding-left:18px;
       position:absolute;
       top:-4px;
    }
</style>
    
 <div id="cyto_div" style="position:absolute; left:0px; top:0px">
    <h3 class="interactions">Interaction Network </h3>
	<p> Your query proteins are represented as red nodes in the network.<br> The other nodes are predicted interactors and the link thickness is 
proportional to the confidence of the prediction <br>(either SVM, RF or an avergae of both scores depending on your selection above).<br>
 The predictions that match known interactions (from BioGRID) are shown in colour as in the table. Use the controls to set the zoom 
level and centre the network.<br>
If no network appears, check your Java settings.
 <p>
      <a style="color: rgb(136, 136, 136); text-decoration: none; background-color: white;" onmouseout="this.style.backgroundColor='white';" onmouseover="this.style.backgroundColor='#f1f1d1';" title="Cytoscape Web" target="_blank" href="http://cytoscapeweb.cytoscape.org">

        Powered  by  <img border="0/" style="vertical-align: middle;" src="/PInt/cytoscape_logo_small.png" height="15" width="15"> Cytoscape Web
      </a>
    </p>
    <div id="caption" style="font-size:12px; font-style:italic">
    <!-- jQuery will add stuff here -->
    </div>

    <div id="cytoscapeweb" width="*" ></div>
    <div id="menu">
    <!-- jQuery will add stuff here -->
    </div>
    <div id="legends">
    <!-- jQuery will add stuff here -->
    </div>
   
</div>   
   
       
            <div id="cytoscapeweb" align=center>        
        </div>
	
    
    );

return(0)
}
###########
sub ID2name{
	my $fin="/var/www/htdocs/PInt/GeneDB_proteincoding.txt";
	open(INFILE, "<$fin") or die("Cannot open file $fin\n");
	my @conv=<INFILE>;
	chomp(@conv);
	close(INFILE);
	
	
	my %common;
	my @words;
	for my $i(0..$#conv){
		@words=split(/\t/,$conv[$i]);
				
		if($words[1]!~/^$/){
			$common{uc$words[0]}=$words[1];
			
		}
		else{
			$common{uc$words[0]}=uc$words[0];
			
		}
	
	}

#print "inside conversion common $common{'SPAC24B11.06C'}  <p>\n";
	
#my @keys=keys%common;
#print "keys at commn @keys<p>\n";
	return(%common);
}
###########
sub name2ID{
	my $fin="/var/www/htdocs/PInt/GeneDB_proteincoding.txt";
	open(INFILE, "<$fin") or die("Cannot open file $fin\n");
	my @conv=<INFILE>;
	close(INFILE);
	chomp(@conv);
#print "@conv"	;
	my %ids;
	
	my @words;
	for my $i(0..$#conv){
		@words=split(/\t/,$conv[$i]);
#print "@words<p>\n"	;
		#if($#words==1){
			
		$ids{uc$words[0]}=uc$words[0];
		#}		
		if($words[1]!~/^$/){
			
			$ids{$words[1]}=uc$words[0];
			#print "$words[1]\t$ids{$words[1]}<p>\n";
		}
	
	}

#	print "inside conversion common  id $ids{'sty1'}, <p>\n";
	
	
	return(%ids);
}
###########
sub getdesc{
	my $fin="/var/www/htdocs/PInt/GeneDB_proteincoding.txt";
	open(INFILE, "<$fin") or die("Cannot open file $fin\n");
	my @conv=<INFILE>;
	chomp(@conv);
	close(INFILE);
	
	my %product;
	
	my @words;
	my %seen;
	for my $i(0..$#conv){
		@words=split(/\t/,$conv[$i]);
		if(defined $words[2] && !defined $seen{uc$words[0]}){
		$product{uc$words[0]}=$words[2];
		$seen{uc$words[0]}=1;
		}
		else{
		$product{uc$words[0]}='NA';	
		}
		#print "$words[1]\t$ids{$words[1]}<p>\n";
		
	
	}

	#print "inside conversion common  id $ids{'sty1'}, <p>\n";
	
		
#my @keys=keys%product;
#print "keys at commn @keys<p>\n";

	return(%product);
}
#######################################################################
sub getcerprotint{
#	my $fin="/var/www/htdocs/PInt/n_aug10_compUY2H_pbort.txt";
	my $fin="/var/www/htdocs/PInt/ap11cerprot_pbort.txt";

	open(INFILE, "<$fin") or die("Cannot open file $fin\n");
	my @conv=<INFILE>;
	chomp(@conv);
	close(INFILE);
	
	my %protcer;
	
	my @words;
	my %seen;
	for my $i(0..$#conv){
			$conv[$i]=~s/c/C/g;
		@words=split(/\t|\s+/,$conv[$i]);
		if( !defined $seen{"$words[0],$words[1]"}){
		$protcer{"$words[0],$words[1]"}=1;

		$protcer{"$words[1],$words[0]"}=1;
		$seen{"$words[0],$words[1]"}=1;
		}
		
		
		
	
	}
	return(%protcer);

}
##################################

sub getpbprotint{
#	my $fin="/var/www/htdocs/PInt/n_aug10compUY2H_pb.txt";

	my $fin="/var/www/htdocs/PInt/ap11_pbprotints.txt";
	open(INFILE, "<$fin") or die("Cannot open file $fin\n");
	my @conv=<INFILE>;
	chomp(@conv);
	close(INFILE);
	
	my %protpb;
	
	my @words;
	my %seen;
	for my $i(0..$#conv){
		$conv[$i]=~s/c/C/g;
		#$conv[$i]=~s/\s+//g;
		@words=split(/\t|\s+/,$conv[$i]);
		if( !defined $seen{"$words[0],$words[1]"}){
		$protpb{"$words[0],$words[1]"}=1;

		$protpb{"$words[1],$words[0]"}=1;
		$seen{"$words[0],$words[1]"}=1;
		}
		#if(($words[0]=~/SPAC19D5.01/ && $words[1]=~/SPAC24B11.06C/) ||($words[1]=~/SPAC19D5.01/ && $words[0]=~/SPAC24B11.06C/) ){
			#print "<p>pyp2 and sty1 found in databases!!!\n";
		#}
		#}
		
		
		
	
	}
	return(%protpb);

}

#############################################

sub getpbgen{
	my $fin="/var/www/htdocs/PInt/ap11genpb.txt";
	open(INFILE, "<$fin") or die("Cannot open file $fin\n");
	my @conv=<INFILE>;
	chomp(@conv);
	close(INFILE);
	
	my %genpb;
	
	my @words;
	my %seen;
	for my $i(0..$#conv){
		$conv[$i]=~s/c/C/g;
		#$conv[$i]=~s/\s+//g;
		@words=split(/\t|\s+/,$conv[$i]);
		if( !defined $seen{"$words[0],$words[1]"}){
		$genpb{"$words[0],$words[1]"}=1;

		$genpb{"$words[1],$words[0]"}=1;
		$seen{"$words[0],$words[1]"}=1;
		}
		#if(($words[0]=~/SPAC19D5.01/ && $words[1]=~/SPAC24B11.06C/) ||($words[1]=~/SPAC19D5.01/ && $words[0]=~/SPAC24B11.06C/) ){
			#print "<p>pyp2 and sty1 found in databases!!!\n";
		#}
		#}
		
		
		
	
	}
	return(%genpb);

}
#############################################################

sub getcergen{
	#my $fin="/var/www/htdocs/PInt/n_feb10gen_pbort.txt";
	my $fin="/var/www/htdocs/PInt/ap11gencer_pbort.txt";
	open(INFILE, "<$fin") or die("Cannot open file $fin\n");
	my @conv=<INFILE>;
	chomp(@conv);
	close(INFILE);
	
	my %gencer;
	
	my @words;
	my %seen;
	for my $i(0..$#conv){
		$conv[$i]=~s/c/C/g;
		#$conv[$i]=~s/\s+//g;
		@words=split(/\t|\s+/,$conv[$i]);
		if( !defined $seen{"$words[0],$words[1]"}){
		$gencer{"$words[0],$words[1]"}=1;

		$gencer{"$words[1],$words[0]"}=1;
		$seen{"$words[0],$words[1]"}=1;
		}
		#if(($words[0]=~/SPAC19D5.01/ && $words[1]=~/SPAC24B11.06C/) ||($words[1]=~/SPAC19D5.01/ && $words[0]=~/SPAC24B11.06C/) ){
			#print "<p>pyp2 and sty1 found in databases!!!\n";
		#}
		#}
		
		
		
	
	}
	return(%gencer);

}


##############################
sub check_genenames{

# De-reference the array list


        my($genelist,$common,$ids)=@_;	

	my (@genelist)=@$genelist;

my(%common) = %$common;
my(%ids) = %$ids;


#print "inside check_genenames<p>\n";
#print "@genelist<p>\n";

my @keys2=keys%ids;

#print"hash test: $keys2[1]\t$ids{$keys2[1]}<p>\n";


	my $finDB="/var/www/htdocs/PInt/proteins_inDB.txt";
	open(INFILE, "<$finDB") or die("Cannot open file $finDB\n");
	my @inDB=<INFILE>;
	my $inDBbuff='';
#print "$inDBbuff at the beginning<p>\n";
	for my $i(0..$#inDB){
		$inDBbuff.=uc$inDB[$i];
	}
####print "later@conv<p>\n";	
	close(INFILE);



	####now check for each protein in list whether it exists and has info in our DB
	my %nonid;
	my %nongenename;
	my %nonDB;
	my @nameok=@genelist;

	#print "$inDBbuff\n";
	
	for my $i(0..$#genelist){
                
		if ($genelist[$i]=~/^SPA|SPB|SPC/i){
			$genelist[$i]=uc$genelist[$i];
		}
		if($genelist[$i]!~/^S/){
                	$genelist[$i]=lc$genelist[$i];
                }
		#print "gene=$genelist[$i]\n";
		if($genelist[$i]!~/^[a-zA-Z0-9.,\s+\s]/){
			
			#print"<p>Gene name $genelist[$i] contains illegal characters a$genelist[$i]a<p>";
		}
		else{
		$genelist[$i]=~s/\s+//g;
	   #print "$i=$genelist[$i]<p>\n";	
		if ($inDBbuff !~/$genelist[$i] /i){  ## the protein is not in DB of predictions
			if(defined $ids{$genelist[$i]}){ ##there is a systematic id
				my $oldname=$genelist[$i];
				$genelist[$i]=$ids{$genelist[$i]};	
					#print "old name $oldname, new $genelist[$i]\n";
					#print "there is a systematic id $genelist[$i]<p>\n";
					$nameok[$i]="ok";
				if($inDBbuff!~/$genelist[$i]/){	##syst id still not in DB
					#print "the protein syst id is not in the DB<p>\n";
					$nonDB{$oldname}=$oldname;		
					$nameok[$i]="no";
							
				}			
			}
			if(! defined $ids{$genelist[$i]} and !defined $common{$genelist[$i]}){  ## id not in geneDB
				if($genelist[$i]=~/^SP/){
				  #print "there is no systematic id<p>\n";
				   $nonid{$genelist[$i]}=$genelist[$i];
				   $nameok[$i]="no";
			
				
				}
				else{
				  $nongenename{$genelist[$i]}=$genelist[$i];
					$nameok[$i]="no";
				   #print "not a gene name<p>\n";
				}
			#$genelist[$i]='';
			}
			#print " $genelist[$i] not in db<p>\n";
		}
		#print "$genelist[$i] inside check names<p>\n";	
		####################start printing messages
		if (defined $nongenename{$genelist[$i]} || defined $nongenename{$common{$genelist[$i]}}){
			print "<p>$nongenename{$genelist[$i]} is not a fission yeast gene name<p>\n";
		}
		else{
			if (defined $nonid{$genelist[$i]}){
				print "<p>$nonid{$genelist[$i]} is not a fission yeast protein coding gene<p>\n";
			}
			if (!defined $nongenename{$genelist[$i]} && !defined $nonid{$genelist[$i]} && defined $nonDB{$genelist[$i]}){
				print "<p>For $nonDB{$genelist[$i]} we do not have features<p>\n";
			}
		}
		}
	}
	#for my $i(0..$#genelist){
		
	#}

	
#	if (defined $nongenename[0]){
#		print "<p>These are not fission yeast gene names:<p>\n@nongenename<p>\n";
#	}
#	if (defined $nonid[0]){
#		print "<p>The following protein names are not fission yeast protein coding genes:<p>\n@nonid<p>\n";
#	}
#	if (defined $nonDB[0]){
#		print "<p>We do not have features for the following proteins:<p>\n@nonid<p>\n";
#	}

	my @newgenelist;
	for my $j(0..$#genelist){
		if($nameok[$j]=~/ok/){	
			push(@newgenelist,$genelist[$j]);
		}
	}
	
	my %seen = ();
	 my @uniqu = grep { ! $seen{$_} ++ } @newgenelist;
	#print "unique @uniqu\n";
	return(@uniqu);
}
#############################
sub test_query {

    my ($dbh) = @_;

    my $string = qq(SELECT * FROM   pred WHERE protein1 ='SPAC24B11.06C'  );

    my $sth_query = $dbh->prepare($string);

	$sth_query->execute();
print "<table border='1'><tr>
<th>id</th>
<th>protein 1</th>
<th>protein2</th>
<th>score 1</th>
<th>score 2</th></tr>";


    while(my  @row = $sth_query->fetchrow()){
    print"<tr><td>"
    .$row[0]."</td><td>"
    .$row[1]."</td><td>"
    .$row[2]."</td><td>"
    .$row[3]."</td><td>"
    .$row[4]."</td></tr>";
    }
print("</table>");
    

}
#################################
#################################################################################
sub connect_to_DB {

    my ($driver, $instance, $host, $port, $cnf_file, $user, $password) = @_;

    my $connect_string =
        "DBI:${driver}:database=${instance};host=${host};port=$port;" .
        "mysql_read_default_file=${cnf_file}";

    # TODO: should have DBI::errstr's in all queries!

    my $dbh = DBI->connect($connect_string, $user, $password)
        or die "ERROR: $DBI::errstr\n";

    if (not defined $dbh) {
        die "Could not connect to database: $DBI::errstr\n";
    }
	#print ("DB connected , everything OK!\n");
    return $dbh;

}


###############################################################################

sub disconnect_from_DB {

    my $dbh = shift;

    $dbh->disconnect()
        or die "Could not disconnect from database: $DBI::errstr\n";

}


###############################################################################




###############################################################################


###############################################################################
#######################

######################################################################################################################################################


###############################################################################

###############################################################################

