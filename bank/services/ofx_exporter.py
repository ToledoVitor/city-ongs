import datetime

from bank.models import BankAccount, Transaction


class OFXStatementExporter:
    def handle(
        account: BankAccount,
        transactions: list[Transaction],
        start_date: datetime.date,
        end_date: datetime.date,
    ):
        def format_dt(dt):
            if isinstance(dt, datetime.date) and not isinstance(
                dt, datetime.datetime
            ):
                dt = datetime.datetime.combine(dt, datetime.time.min)
            return dt.strftime("%Y%m%d%H%M%S")

        dtstart = format_dt(start_date)
        dtend = format_dt(end_date)
        dtnow = datetime.datetime.now().strftime("%Y%m%d%H%M%S")

        stmttrn_items = []
        for idx, t in enumerate(transactions, start=1):
            trntype = "DEBIT" if t.amount < 0 else "CREDIT"

            dtposted = format_dt(t.date)
            fitid = f"{dtnow}{idx}"

            stmttrn_items.append(f"""
                <STMTTRN>
                    <TRNTYPE>{trntype}</TRNTYPE>
                    <DTPOSTED>{dtposted}</DTPOSTED>
                    <TRNAMT>{t.amount}</TRNAMT>
                    <FITID>{fitid}</FITID>
                    <NAME>{t.name}</NAME>
                </STMTTRN>
            """)

        stmttrn_items_str = "\n".join(stmttrn_items)
        ofx_content = f"""OFXHEADER:100
            DATA:OFXSGML
            VERSION:102
            SECURITY:NONE
            ENCODING:USASCII
            CHARSET:1252
            COMPRESSION:NONE
            OLDFILEUID:NONE
            NEWFILEUID:NONE

            <OFX>
            <SIGNONMSGSRSV1>
            <SONRS>
                <STATUS>
                <CODE>0</CODE>
                <SEVERITY>INFO</SEVERITY>
                </STATUS>
                <DTSERVER>{dtnow}</DTSERVER>
                <LANGUAGE>POR</LANGUAGE>
            </SONRS>
            </SIGNONMSGSRSV1>
            <BANKMSGSRSV1>
            <STMTTRNRS>
                <TRNUID>1</TRNUID>
                <STATUS>
                <CODE>0</CODE>
                <SEVERITY>INFO</SEVERITY>
                </STATUS>
                <STMTRS>
                <CURDEF>BRL</CURDEF>
                <BANKACCTFROM>
                    <BANKID>{account.bank_id}</BANKID>
                    <ACCTID>{account.account}</ACCTID>
                    <ACCTTYPE>{account.account_type.upper()}</ACCTTYPE>
                </BANKACCTFROM>
                <BANKTRANLIST>
                    <DTSTART>{dtstart}</DTSTART>
                    <DTEND>{dtend}</DTEND>
                    {stmttrn_items_str}
                </BANKTRANLIST>
                <LEDGERBAL>
                    <BALAMT>{account.balance}</BALAMT>
                    <DTASOF>{dtnow}</DTASOF>
                </LEDGERBAL>
                </STMTRS>
            </STMTTRNRS>
            </BANKMSGSRSV1>
            </OFX>
        """

        return ofx_content
