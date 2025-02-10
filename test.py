import phonenumbers
x = [phonenumbers.parse("asd96576616 34 56 78", "ES"), phonenumbers.parse("+34 616 34 56 78", "ES"), phonenumbers.parse("0034 616 34 56 78", "ES"), phonenumbers.parse("34 616 34 56 78", "ES")]


y = [phonenumbers.format_number(i, phonenumbers.PhoneNumberFormat.E164) for i in x]
print(y)