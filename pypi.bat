@echo off

if defined HOME set temp_home=%HOME%
set HOME=%USERPROFILE%

if [%1]==[] goto nocommand
if %1==register goto get_target
if %1==upload goto get_target
goto nocommand

:end
if defined temp_home (set HOME=%temp_home%) else (set HOME=)
exit /b

:get_target
if [%2]==[] (goto notarget) else (goto %1)

:nocommand
echo .
echo Valid commands are 
echo   register
echo   upload
echo .
echo Examples:
echo   pypi.bat register test
echo   pypi.bat register pypi
echo   pypi.bat upload test
echo   pypi.bat upload pypi
goto end

:notarget
echo You must specify a target (check .pypirc)
echo .
echo Examples:
echo   pypi.bat register test
echo   pypi.bat register pypi
echo   pypi.bat upload test
echo   pypi.bat upload pypi
goto end

:upload

rmdir /S /Q dist
rmdir /S /Q build
rmdir /S /Q friendlysam.egg-info
python setup.py sdist bdist_wheel bdist_wininst
twine upload --repository %2 dist/*

goto end

:register
python setup.py register -r %2

goto end

