"""
mail_processor.py
Minimaler Mail → NLU → LLM → Send Processor
"""
from typing import Dict
from agents.enhanced_email_agent import EnhancedEmailAgent


class MailProcessor:
    def __init__(self):
        self.agent = EnhancedEmailAgent()

    def run_once(self) -> int:
        """Verarbeitet eine Runde ungelesener E-Mails und gibt Anzahl verarbeiteter Mails zurück."""
        return self.agent.process_emails()


def get_mail_processor() -> MailProcessor:
    return MailProcessor()


if __name__ == '__main__':
    mp = MailProcessor()
    count = mp.run_once()
    print(f"Verarbeitete E-Mails: {count}")


