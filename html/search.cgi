#!/usr/local/bin/perl

# The Xavatoria Indexed Search Engine, Version 1.0
#	Copyright 1997 by Fluid Dynamics <xav.com>
#
# For latest version and help files, visit:
#	http://www.xav.com/scripts/search/
# __________________________________________________________________


# Location of your index file:

#$Index_File = "/u2/home/xav/search/index.txt";
$Index_File = "/usr2/info/pubs/periodicals/tog/resources/RTNews/html/search_index.txt";

# Words that are generally ignored in a search query:

$Ignore .= " what how who which when where do you find site get and ";
$Ignore .= " or if not a the for an it of from by the one two to he ";
$Ignore .= " most all about i me search is are be been with why ";

# The URL to your main search page with tips and so on:

$Search_Page = "http://www.acm.org/tog/resources/RTNews/html/search.html";

# How many links should the viewer see per page?

$Hits_Per_Page = 10;

# This forms a hyperlink back to your main web page:

($Link_URL,$Link_Title) = ("http://www.acm.org/tog/resources/RTNews/html/index.html","Ray Tracing News Guide Page");

# The HTML for the top of the search results page.  Ours is pretty 
# generic and should work if you aren't too creative.  Edit between 
# the lines containing "EOM":

$Header = <<EOM;
<HTML>
<HEAD>
<TITLE>Search Results</TITLE>
</HEAD>
<BODY BGCOLOR="#FFFFFF">
<H2><TT>Ray Tracing News Search Results</TT></H2>
EOM

# The HTML to give searchers who can't seem to find anything. Usually 
# this should include yet another link back to the tips page, and, if 
# you're a business that is not overly annoyed by people sending you 
# email, a mailto: link for them to request information from a human 
# would be in order here:

$No_Documents_Found = <<EOM;
<BLOCKQUOTE>
<B>Unfortunately, we didn't find any documents which matched your 
search terms. You may want to visit the <A HREF="search.html">search 
tips</A> page to better refine your queries.<BR>
<BR>If all else fails, write Eric Haines at <A HREF="mailto:erich\@acm.org">
erich\@acm.org</A>.</B>
</BLOCKQUOTE>
EOM

# The location of your summaries file.  It holds information about who 
# searched for what, what they found, and so on.  This provides pretty 
# good feedback on your visitors.  Make this file writable (chmod 777):

$summary_file = "/usr2/users/erich/summaries_rtn.html";

# No further editing is necessary, but feel free to play around...
# 
# __________________________________________________________________


if ($ENV{'QUERY_STRING'} =~ /^Range=([^\&]*)\&Format=([^\&]*)\&Terms=([^\&]*)\&Rank=(.*)/i)
	{
	($Range,$Format,$terms,$rank) = ($1,$2,$3,$4);
	$Encoded_Terms = $terms;
	$terms =~ tr/+/ /;
	$terms =~ s/%([a-fA-F0-9][a-fA-F0-9])/pack("C",hex($1))/eg;
	$Saved_Terms = $terms;
	}
elsif ($ENV{'QUERY_STRING'} =~ /^Range=([^\&]*)\&Format=([^\&]*)\&Terms=([^\&]*)/i)
	{
	($Range,$Format,$terms,$rank) = ($1,$2,$3,1);
	$Encoded_Terms = $terms;
	$terms =~ tr/+/ /;
	$terms =~ s/%([a-fA-F0-9][a-fA-F0-9])/pack("C",hex($1))/eg;
	$Saved_Terms = $terms;
	}
else
	{
	print "Location: $Search_Page\n\n";
	exit;
	}
$terms = " " . $terms . " ";
$terms =~ s/\s+/ /g;
@Raw_Terms = split(/\"/,$terms);
$terms = "";
foreach $term (@Raw_Terms)
	{
	if ($i == 1)
		{$i--;}
	else
		{$i++;}
	$term =~ s/ /_/g unless $i;
	$terms .= $term;
	}
$terms =~ s/ not / -/ig;
$terms =~ s/ and / \+/ig;
$terms =~ s/ or / \|/ig;
$WildCard = "thewildcardisaveryspecialcharacter";
$terms =~ s/(\*+)/$WildCard/g;
@terms = split(/\s+/,$terms);
foreach $term (@terms)
	{
	next if ($term eq "");
	if (($Ignore =~ / $term /i) && ($term !~ /^\W/))
		{
		$Ignored_Terms .= $term . ", ";
		next;
		}
	if ($term =~ /$WildCard/)
		{
		$Beta = $term;
		$Beta =~ s/$WildCard//g;
		$Beta =~ s/\W//g;
		$Beta =~ s/_//g;
		if (length($Beta) < 3)
			{
			$Ignored_Terms .= $term . ", ";
			next;
			}
		}
	$term =~ s/_/ /g;
	if ($term =~ /^-/)
		{
		if ($term =~ / /)
			{
			$Ignored_Terms .= "\"" . $term . "\", ";
			}
		else
			{
			$Ignored_Terms .= $term . ", ";
			}
		push(@forbidden,&Format_Term($term));
		}
	elsif (($term =~ /^\|/) || (($Range eq "Any") && ($term !~ /^\+/)))
		{
		if ($term =~ / /)
			{
			$Important_Terms .= "\"" . $term . "\", ";
			}
		else
			{
			$Important_Terms .= $term . ", ";
			}
		push(@optional,&Format_Term($term));
		}
	else
		{
		if ($term =~ / /)
			{
			$Important_Terms .= "\"" . $term . "\", ";
			}
		else
			{
			$Important_Terms .= $term . ", ";
			}
		push(@required,&Format_Term($term));
		}
	}
$delimiter = '%%==%%';
open(ALLFILE,"$Index_File") || &Fatal;
foreach $LINE (<ALLFILE>)
	{
	($Crank,$URL,$Title,$Description,$Size,$Last_Modified,$string) = split(/$delimiter/,$LINE);
	$string =~ s/\n/ /g;
	($Relevance,$Kill) = (0,0);
	foreach (@forbidden)
		{
		if (($string =~ /$_/i) && ($_ !~ /[A-Z]/))
			{
			$Kill++;
			last;
			}
		elsif ($string =~ /$_/)
			{
			$Kill++;
			last;
			}
		}
	next if ($Kill);
	foreach (@required)
		{
		if (($string =~ /$_/) && ($_ =~ /[A-Z]/))
			{
			$Relevance += (($string =~ s/$_/$_/og) + 20);
			}
		elsif (($string =~ /$_/i) && ($_ !~ /[A-Z]/))
			{
			$Relevance += (($string =~ s/$_/$_/oig) + 10);
			}
		else
			{
			$Kill++;
			last;
			}
		}
	next if ($Kill);
	foreach (@optional)
		{
		if (($string =~ /$_/) && ($_ =~ /[A-Z]/))
			{
			$Relevance += ($string =~ s/$_/$_/og);
			}
		elsif (($string =~ /$_/i) && ($_ !~ /[A-Z]/))
			{
			$Relevance += ($string =~ s/$_/$_/oig);
			}
		}
	&Include if ($Relevance);
	}
close(ALLFILE);
if ($Ignored_Terms =~ /(.*)\, /)
	{
	$Ignored_Terms = " " . $1;
	$Ignored_Terms =~ s/$WildCard/\*/g;
	$Ignored_Terms =~ s/ (\"?)\-/ $1/g;
	$summary .= "Ignored: <TT>$Ignored_Terms</TT>.<BR>\n";
	}
else
	{
	$summary .= "<BR>\n";
	}
if ($Important_Terms =~ /(.*)\, /)
	{
	$Important_Terms = " " . $1;
	$Important_Terms =~ s/$WildCard/\*/g;
	$Important_Terms =~ s/ (\"?)\+/ $1/g;
	$Important_Terms =~ s/ (\"?)\|/ $1/g;
	$summary .= "Searched for: <TT>$Important_Terms</TT>.<BR>\n";
	}
$Remaining = ($hitcount - $rank) - ($Hits_Per_Page - 1);
if ($Remaining > $Hits_Per_Page)
	{
	$Next = $Hits_Per_Page;
	$New_Rank = $rank + $Hits_Per_Page;
	}
elsif ($Remaining > 0)
	{
	$Next = $Remaining % $Hits_Per_Page;
	$New_Rank = $rank + $Hits_Per_Page;
	}
else
	{
	$New_Rank = $hitcount + 1;
	}
$summary .= "Displaying documents " . $rank . "-" . ($New_Rank - 1);
$summary .= " of $hitcount, with best matches first.<BR>\n";
if (($summary_file) && (-e $summary_file))
	{
	open(SUMMARY,">>$summary_file");
	print SUMMARY "Search by $ENV{'REMOTE_HOST'}:<BR>\n";
	print SUMMARY "Raw Query was: $Saved_Terms<BR>\n";
	print SUMMARY "$summary\n<BR><HR><BR>\n";
	close(SUMMARY);
	}
print "Content-type: text/html\n\n";
print $Header;
print $summary;
if ($hitcount > 0)
	{
	if ($Format eq "Standard")
		{
		print "<BR>\n<BLOCKQUOTE>\n<DL>\n";
		}
	else
		{
		print "<BR>\n<PRE>\n";
		}
	$i = 0;
	foreach $key (reverse sort keys %HITS)
		{
		$i++;
		next if ($i < $rank);
		next if ($i > ($rank + ($Hits_Per_Page - 1)));
		($URL,$Title,$Description,$Size,$Last_Modified) = split(/$delimiter/,$HITS{$key});
		if ($Format eq "Standard")
			{
			if ($Size < 1500)
				{
				$Size = "$Size bytes";
				}
			else
				{
				$Size = int($Size/1000) . " K";
				}
			print "<P><DT><A HREF=\"$URL\"><STRONG>$Title</STRONG></A></DT>";
			print "<DD>$Description<BR>\n<CITE><A HREF=\"$URL\">$URL</A>";
			print "<FONT SIZE=-1> - $Size - $Last_Modified</FONT></CITE></DD>\n";
			}
		else
			{
			&Compact_Print;
			}
		}
	if ($Format eq "Standard")
		{
		print "</DL>\n";
		}
	else
		{
		print "</PRE>\n";
		}

	print "Documents " . $rank . "-" . ($New_Rank - 1);
	print " of $hitcount displayed.<BR>\n";
	print "</BLOCKQUOTE>\n" if ($Format eq "Standard");
	print "<CENTER>\n";
	if ($Remaining > 0)
		{
		print "<A HREF=\"$ENV{'SCRIPT_NAME'}?Range=$Range\&Format=$Format\&Terms=$Encoded_Terms\&Rank=$New_Rank\">";
		print "<H4>Next $Next Matches</H4></A>\n";
		}
	}
else
	{
	print $No_Documents_Found;
	}

$Saved_Terms =~ s/\"/\&#34;/g;
print <<EOM;
<BR>
<CENTER>
<FORM METHOD=GET ACTION="$ENV{'SCRIPT_NAME'}">
<B>Match 
<SELECT NAME="Range">
EOM

if (($Range eq "All") && ($hitcount))
	{
	print "<OPTION VALUE=\"All\" SELECTED>All Terms";
	print "<OPTION VALUE=\"Any\">Any Term";
	}
else
	{
	print "<OPTION VALUE=\"All\">All Terms";
	print "<OPTION VALUE=\"Any\" SELECTED>Any Term";
	}

print <<EOM;
</SELECT>
and show results 
<SELECT NAME="Format">
EOM
if ($Format eq "Standard")
	{
	print "<OPTION VALUE=\"Standard\" SELECTED>in Standard Form";
	print "<OPTION VALUE=\"Compact\">in Compact Form";
	}
else
	{
	print "<OPTION VALUE=\"Standard\">in Standard Form";
	print "<OPTION VALUE=\"Compact\" SELECTED>in Compact Form";
	}
print <<EOM;
</SELECT></B><BR>
<INPUT NAME="Terms" SIZE=45 MAXLENGTH=800 VALUE="$Saved_Terms">
<INPUT TYPE=submit VALUE=" New Search ">
</FORM></CENTER>
<BR><H5 ALIGN=CENTER>
<A HREF="$Search_Page">Search Tips</A> - 
<A HREF="$Link_URL">$Link_Title</A><HR SIZE=1 NOSHADE WIDTH=50\%>
The Xavatoria Search Engine is Copyright 1997 by 
<A HREF="http://www.xav.com">Fluid Dynamics</A>.<BR>
Visit the <A HREF="http://www.xav.com/scripts/search">Search Page</A> 
for help files and most recent version.</H5></BODY></HTML>
EOM
sub Include
{
$Relevance = ($Relevance * $Crank) if ($Crank > 1);
$Relevance = 100000 if ($Relevance > 100000);
$Relevance = sprintf("%.5f",($Relevance/100000));
$HITS{"$Relevance$URL"} = $URL . $delimiter . $Title . $delimiter . $Description . $delimiter. $Size . $delimiter . $Last_Modified;
$hitcount++;
}

sub Compact_Print
{
if (length($Title) < 25)
	{
	while (length($Title) < 25)
		{
		$Title .= " ";
		}
	}
else
	{
	@Title_Characters = split(//,$Title);
	$Title = "";
	for ($x=0; $x<25; $x++)
		{
		$Title .= $Title_Characters[$x];
		}
	}
if (length($Description) < 36)
	{
	while (length($Description) < 36)
		{
		$Description .= " ";
		}
	}
else
	{
	@Descript_Characters = split(//,$Description);
	$Description = "";
	for ($x=0; $x<36; $x++)
		{
		$Description .= $Descript_Characters[$x];
		}
	}
if (length($Last_Modified) == 8)
	{
	$Last_Modified = "0" . $Last_Modified;
	}
print "<A HREF=\"$URL\">$Title</A> [$Last_Modified] $Description\n";
}
sub Format_Term
{
$_ = shift;
$_ = " " . $_ . " ";
$_ =~ s/\W/ /g;
$_ =~ s/\s+/ /g;
$_ =~ s/$WildCard/\(\[\^\\s\+\]\{0,4\}\)/g;
return $_;
}
sub Fatal
{
print "Content-type: text/plain\n\n";
print "Fatal Error: Could not read from the index file.\n";
print "Check location at $Index_File.\n\n";
exit;
}
