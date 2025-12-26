
Command-line Options:

--clean-db - Clean database before running tests
--debug - Enable verbose debug output
--flow=<name> - Run specific flow (auth, settings, team, or all)
--help - Show usage information

# Run all tests with clean database
./e2e_test.sh --clean-db

# Run only auth flow with debug
./e2e_test.sh --flow=auth --debug

# Run settings flow (includes auth) with clean db
./e2e_test.sh --clean-db --flow=settings --debug

# Run all flows
./e2e_test.sh --flow=all --clean-db