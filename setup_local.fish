#!/usr/bin/fish

set -l envfile ".env"
if [ (count $argv) -gt 0 ]
  set envfile $argv[1]
end

if test -e $envfile
  for line in (cat $envfile)
    set -xg (echo $line | cut -d = -f 1) (echo $line | cut -d = -f 2-)
  end
end
