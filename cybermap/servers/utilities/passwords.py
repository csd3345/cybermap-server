import cryptography.fernet
import pickle


def store_sudo_password(mode: str):
    available_modes = ["pickles", "keyring"]
    
    mode = mode.lower()
    if mode not in available_modes:
        raise NotImplementedError(f"Mode {mode} is not implemented yet. "
                                  f"Available modes are [{', '.join(available_modes)}]")
    
    # at this point we want to make sure that the SUDO password is correctly stored in the process
    if mode == "pickles":
        pass
        # check if the password pickle object exists (if it does then a password was already provided by the user)
        # if Path(global_options["sudo"]["password_pickle"]).exists():
        #     __logger.info("Found password pickle")
        #     # check for cipher_pickle
        #     if not Path(global_options["sudo"]["cipher_pickle"]).exists():
        #         __logger.warning("Cipher pickle is missing. Password retrieval impossible")
        #         __logger.warning(f"Sudo password must be reconfigured, but first file "
        #                          f"{colorize(global_options['sudo']['password_pickle'], 'gold_1')} "
        #                          f"must be deleted.")
        #         if not confirmation(
        #                 f"Do you want to delete {colorize(global_options['sudo']['password_pickle'], 'gold_1')} now"):
        #             __logger.info("As you wish. The program will terminate now.")
        #             sys.exit()
        #         Path(global_options["sudo"]["password_pickle"]).unlink()
        #         __logger.info(f"{colorize(global_options['sudo']['password_pickle'], 'gold_1')} file removed.")
        #         __logger.info(f"You can {colorize('restart')} the program now to reconfigure the password.")
        #         sys.exit()
        #     else:
        #         __logger.info("Found cipher pickle")
        #
        #     with Path(global_options["sudo"]["cipher_pickle"]).open(mode = "rb") as file:
        #         __logger.info("Loading Cipher key")
        #         cipher_key = pickle.load(file)
        #         __logger.info(f"Cipher key: {colorize(cipher_key, 'gold_1')}")
        #
        #     with Path(global_options["sudo"]["password_pickle"]).open(mode = "rb") as file:
        #         __logger.info("Loading Ciphered text")
        #         ciphered_text = pickle.load(file)
        #         __logger.info(f"Ciphered text: {colorize(ciphered_text, 'gold_1')}")
        #
        #     cipher_suite = cryptography.fernet.Fernet(key = cipher_key)
        #     sudo_password = cipher_suite.decrypt(ciphered_text)
        #     print(sudo_password)
        # else:
        #     __logger.info("Sudo password was not found in database")
        #     configure_sudo_password()  # ask the user for sudo password
        #     __logger.debug(f"New sudo password: {colorize(global_options['sudo']['password'], 'gold_1')}")


def configure_sudo_password(self):
    password: str = str()
    try:
        while not password:
            password: str = click.prompt(
                f"{time_colored()} Please enter sudo password",
                hide_input = True,
                type = str,
            )
            
            if not password:
                _logger.warning("Password cannot be empty. Try again.")
                continue
            
            confirmed_password = click.prompt(
                f"{time_colored()} Repeat sudo password for confirmation",
                hide_input = True,
                type = str,
            )
            if not password == confirmed_password:
                _logger.warning("Passwords did not match. Try again.")
                password = str()
                continue
            
            password: bytes = password.encode("utf-8")
        
        # pickle password for later use
        with Path(self.options.sudo_cipher_pickle).open(mode = "wb") as file:
            cipher_key: bytes = cryptography.fernet.Fernet.generate_key()
            pickle.dump(cipher_key, file)
        
        with Path(self.options.sudo_password_pickle).open(mode = "wb") as file:
            cipher_text: bytes = cryptography.fernet.Fernet(cipher_key).encrypt(password)
            pickle.dump(cipher_text, file)
        
        self.options.set(sudo_password = password)
    except click.Abort:
        _logger.info("Re-run the program to configure the sudo password.")
        sys.exit()
