"""Evaluation scenarios for the VAPI Debt Collection Agent (Divya / HDFC Bank).

4 scenarios, each 5-10 turns.
Account: 123456789 | Customer: Chintan | Due: ₹12,000 on 1st March 2026
Overdue by 4 days (today = 7th March). Promised to pay 3rd March (missed).

Each turn dict:
  input               – text the simulated user says (STT transcript style)
  golden_text         – what Divya SHOULD respond (guidance for judge)
  required_function_call – {name, args} or None
  function_call_response – mock server response returned to the LLM after the call
"""

# =============================================================================
# SCENARIO 1 — Happy Path: Payment Already Done
# Flow: Greeting → Identity Confirmed → Reason → Payment Done → Call Closing
# =============================================================================

scenario_1_payment_done = [
    # Turn 0 – Agent identifies self; user confirms identity
    {
        "input": "Haan, main Chintan bol raha hoon.",
        "golden_text": (
            "तो Chintan ji, main aapko HDFC Bank ke personal loan ke baare mein "
            "call kar rahi hoon — account ke last four digits six seven eight nine. "
            "Aapka twelve thousand rupees ka payment 1st March ko due tha, "
            "aur aapne 3rd March ko pay karne ka promise kiya tha, "
            "lekin abhi tak payment receive nahi hui hai. "
            "Kya aapne already payment kar di hai?"
        ),
        "required_function_call": None,
    },
    # Turn 1 – User says they paid on 5th March via UPI
    {
        "input": "Haan, maine 5 March ko UPI se pay kar diya tha.",
        "golden_text": (
            "Achha, aur kitna amount pay kiya tha aapne?"
        ),
        "required_function_call": None,
    },
    # Turn 2 – User gives exact amount; agent confirms details
    {
        "input": "Poore 12000 rupaye.",
        "golden_text": (
            "Toh confirm karu — aapne 5th March ko UPI se twelve thousand rupees pay kiye. Sahi hai?"
        ),
        "required_function_call": None,
    },
    # Turn 3 – User confirms; agent records payment
    {
        "input": "Haan, sahi hai.",
        "golden_text": (
            "Aapki payment details record kar leti hoon... "
            "Aapki payment details record ho gayi hain. "
            "Yeh 1-3 business days mein system mein reflect ho jaayegi."
        ),
        "required_function_call": {
            "name": "recordPayment",
            "args": {
                "accountNumber": "123456789",
                "paymentDate": "2026-03-05",
                "paymentMode": "upi",
                "amount": 12000,
            },
        },
        "function_call_response": {"status": "success", "message": "Payment recorded."},
    },
    # Turn 4 – User acknowledges; agent closes call
    {
        "input": "Theek hai, shukriya.",
        "golden_text": (
            "Aapka time dene ke liye dhanyavaad, Chintan ji. "
            "Agar koi sawaal ho toh aap HDFC customer care ko contact kar sakte hain. "
            "Have a good day!"
        ),
        "required_function_call": None,
    },
]

# =============================================================================
# SCENARIO 2 — Promise to Pay Later (Hindi throughout)
# Flow: Greeting → Reason → Not Paid → Promise to Pay → Call Closing
# =============================================================================

scenario_2_promise_to_pay = [
    # Turn 0 – User confirms identity in Hindi
    {
        "input": "जी, मैं Chintan हूँ।",
        "golden_text": (
            "तो Chintan जी, आपके personal loan account — last four digits six seven eight nine — "
            "पर twelve thousand rupees का payment 1st March को due था। "
            "आपने 3rd March को pay करने का promise किया था लेकिन payment अभी तक नहीं आयी। "
            "क्या आपने payment की है?"
        ),
        "required_function_call": None,
    },
    # Turn 1 – User says they haven't paid yet
    {
        "input": "नहीं, अभी नहीं की। थोड़ी परेशानी थी इस महीने।",
        "golden_text": (
            "मैं समझ सकती हूँ, Chintan जी — कभी-कभी ऐसा हो जाता है। "
            "अभी तक कोई credit impact नहीं हुआ है, लेकिन late fee लग सकती है। "
            "कब तक आप payment कर पाएंगे?"
        ),
        "required_function_call": None,
    },
    # Turn 2 – User gives a date
    {
        "input": "अगले शुक्रवार तक कर दूँगा, मतलब 14 March.",
        "golden_text": (
            "ठीक है, Chintan जी — तो आप full twelve thousand rupees pay करेंगे? "
            "और कौनसा mode prefer करेंगे — bank transfer, UPI, या online?"
        ),
        "required_function_call": None,
    },
    # Turn 3 – User confirms amount and mode; agent repeats for confirmation
    {
        "input": "हाँ, पूरे 12000. UPI से करूँगा।",
        "golden_text": (
            "तो confirm करूँ — आप twelve thousand rupees, 14th March को UPI से pay करेंगे। सही है?"
        ),
        "required_function_call": None,
    },
    # Turn 4 – User confirms; agent triggers tool and closes
    {
        "input": "हाँ सही है।",
        "golden_text": (
            "आपकी payment commitment set up कर देती हूँ... "
            "बहुत अच्छा, Chintan जी। आपका commitment record हो गया है। "
            "आपका time देने के लिए धन्यवाद। Have a good day!"
        ),
        "required_function_call": {
            "name": "createPromiseToPay",
            "args": {
                "accountNumber": "123456789",
                "promiseDate": "2026-03-14",
                "promiseAmount": 12000,
                "paymentMode": "upi",
            },
        },
        "function_call_response": {"status": "success", "message": "Promise to pay recorded."},
    },
]

# =============================================================================
# SCENARIO 3 — Refusal → Human Handoff for Settlement
# Flow: Greeting → Reason → Refuse to Pay → transferCall (settlement)
# =============================================================================

scenario_3_settlement = [
    # Turn 0 – User confirms identity
    {
        "input": "Yes, this is Chintan.",
        "golden_text": (
            "Hi Chintan, I'm calling regarding your personal loan — "
            "last four digits six seven eight nine — where twelve thousand rupees "
            "were due on 1st March. You had promised to pay by 3rd March "
            "but the payment hasn't come through yet. "
            "Have you already made the payment?"
        ),
        "required_function_call": None,
    },
    # Turn 1 – User says they can't pay at all
    {
        "input": "I lost my job last month. I honestly can't pay right now.",
        "golden_text": (
            "I'm really sorry to hear that, Chintan — that is a very tough situation. "
            "Since you're within the first 30 days overdue, there's no credit impact yet, "
            "but a late fee may apply. "
            "Would you be able to pay even a partial amount for now?"
        ),
        "required_function_call": None,
    },
    # Turn 2 – User insists they can't pay anything; asks about settlement
    {
        "input": "No, I really can't pay anything right now. Is there any way to settle for less?",
        "golden_text": (
            "I understand, Chintan. For settlement options, "
            "I'll connect you with our team who can discuss "
            "the best arrangement for your situation..."
        ),
        "required_function_call": {
            "name": "transferCall",
            "args": {
                "accountNumber": "123456789",
                "reason": "settlement_request",
            },
        },
        "function_call_response": {"status": "transferred"},
    },
]

# =============================================================================
# SCENARIO 4 — Quick Callback Request
# Flow: Greeting → User busy → scheduleCallback → Call Closing
# =============================================================================

scenario_4_callback = [
    # Turn 0 – User confirms identity but says they are driving
    {
        "input": "Haan main Chintan hun, lekin main driving kar raha hoon abhi.",
        "golden_text": (
            "Bilkul, Chintan ji — koi baat nahi. "
            "Main aapko baad mein call kar sakti hoon. "
            "Kab aur kitne baje call karna theek rahega?"
        ),
        "required_function_call": None,
    },
    # Turn 1 – User gives callback time
    {
        "input": "Kal shaam 5 baje call karo.",
        "golden_text": (
            "I'll schedule a callback for you... "
            "Theek hai, main aapko kal — 8th March — shaam 5 baje call karungi. "
            "Aapka time dene ke liye dhanyavaad, Chintan ji. Drive safe!"
        ),
        "required_function_call": {
            "name": "scheduleCallback",
            "args": {
                "accountNumber": "123456789",
                "callbackDate": "2026-03-08",
                "callbackTime": "5:00 PM",
                "reason": "Customer was unavailable, requested callback to discuss overdue payment",
            },
        },
        "function_call_response": {"status": "success", "message": "Callback scheduled."},
    },
]

# =============================================================================
# Combined turns list — all scenarios flattened sequentially.
# The eval framework runs them as one continuous conversation unless
# you use --only-turns to isolate a specific scenario's range.
#
# Scenario 1: turns 0–3   (4 turns)
# Scenario 2: turns 4–8   (5 turns)
# Scenario 3: turns 9–14  (6 turns)
# Scenario 4: turns 15–16 (2 turns)
# =============================================================================


# =============================================================================
# scenario_family_emergency_extension_request
# =============================================================================

scenario_family_emergency_extension_request = [
    # Turn 0 – User confirms identity
    {
        "input": "हाँ, मैं Chintan बोल रहा हूँ।",
        "golden_text": (
            "नमस्ते Chintan जी, मैं Divya बोल रही हूँ HDFC Bank से। "
            "तो आपके personal loan account — last four digits 6789 — पर 12,000 रुपये का payment 1st March को due था। "
            "आपने 3rd March को pay करने का promise किया था लेकिन अभी तक payment receive नहीं हुई है। क्या आपने payment कर दी है?"
        ),
        "required_function_call": None,
    },
    # Turn 1 – User mentions family emergency
    {
        "input": "नहीं, घर में emergency थी, एक close relative का देहांत हो गया था, इसलिए payment नहीं कर पाया।",
        "golden_text": (
            "अच्छा Chintan जी, मुझे ये सुनकर बहुत दुख हुआ — ऐसी situation में manage करना मुश्किल होता है। "
            "मैं समझ सकती हूँ कि आप payment नहीं कर पाए, लेकिन अभी payment 4 दिन overdue है और late fee लग सकती है। "
            "आप कब तक payment arrange कर पाएंगे?"
        ),
        "required_function_call": None,
    },
    # Turn 2 – User asks for extension
    {
        "input": "मुझे थोड़ा time चाहिए, शायद 10-12 दिन लग जाएंगे। आप मुझे 18 March को सुबह 11 बजे call कर लेना।",
        "golden_text": (
            "ठीक है Chintan जी, मैं समझ सकती हूँ कि आपको थोड़ा extra time चाहिए। "
            "I'll schedule a callback for you... "
            "तो क्या मैं 18th March को आपको call करूँ ताकि हम payment status check कर सकें?"
        ),
        "required_function_call": {
            "name": "scheduleCallback",
            "args": {
                "accountNumber": "123456789",
                "callbackDate": "2026-03-18",
                "callbackTime": "11:00 AM",
                "reason": "Customer requested time due to family emergency"
            }
        },
        "function_call_response": {
            "status": "scheduled"
        }
    },
    # Turn 3 – User later commits to partial payment; agent confirms details
    {
        "input": "ठीक है, मैं 18 March को 6000 UPI से दे दूंगा पहले, बाकी बाद में।",
        "golden_text": (
            "तो confirm करूँ — आप 6,000 रुपये 18th March को UPI से pay करेंगे। सही है?"
        ),
        "required_function_call": None,
    },
    # Turn 4 – User confirms; agent triggers tool and closes
    {
        "input": "हाँ, सही है।",
        "golden_text": (
            "आपकी payment commitment set up कर देती हूँ... "
            "ठीक है Chintan जी, आपका commitment note कर लिया गया है। "
            "कृपया ensure करें कि payment time पर हो जाए ताकि आगे charges avoid हो सकें। "
            "धन्यवाद, आपका दिन शुभ हो।"
        ),
        "required_function_call": {
            "name": "createPromiseToPay",
            "args": {
                "accountNumber": "123456789",
                "promiseDate": "2026-03-18",
                "promiseAmount": 6000,
                "paymentMode": "upi"
            }
        },
        "function_call_response": {
            "status": "success"
        }
    }
]


# =============================================================================
# scenario_user_not_available_requests_callback
# =============================================================================

scenario_user_not_available_requests_callback = [
    # Turn 0 – User confirms identity but is busy
    {
        "input": "हाँ मैं Chintan बोल रहा हूँ, लेकिन अभी मैं meeting में हूँ।",
        "golden_text": (
            "नमस्ते Chintan जी, मैं Divya बोल रही हूँ HDFC Bank से। "
            "तो आपके personal loan account — last four digits 6789 — पर 12,000 रुपये का payment 1st March को due था। "
            "आपने 3rd March को pay करने का promise किया था लेकिन अभी तक payment receive नहीं हुई है — क्या आपने payment कर दी है?"
        ),
        "required_function_call": None,
    },
    # Turn 1 – User says cannot talk now and asks for callback
    {
        "input": "अभी बात नहीं कर सकता, बाद में call कर लेना।",
        "golden_text": (
            "अच्छा Chintan जी, मैं समझ सकती हूँ कि आप अभी busy हैं। "
            "I'll schedule a callback for you... "
            "आपको किस time पर call करना convenient रहेगा?"
        ),
        "required_function_call": None,
    },
    # Turn 2 – User provides callback time
    {
        "input": "शाम को 6 बजे call कर लेना।",
        "golden_text": (
            "I'll schedule a callback for you... "
            "तो confirm करूँ — मैं आपको 7th March को शाम 6 बजे call करूँगी ताकि हम payment के बारे में बात कर सकें।"
        ),
        "required_function_call": {
            "name": "scheduleCallback",
            "args": {
                "accountNumber": "123456789",
                "callbackDate": "2026-03-07",
                "callbackTime": "6:00 PM",
                "reason": "Customer is busy in meeting and requested callback"
            }
        },
        "function_call_response": {
            "status": "scheduled"
        }
    },
    # Turn 3 – Call closing
    {
        "input": "ठीक है।",
        "golden_text": (
            "ठीक है Chintan जी, मैंने आपका callback schedule कर दिया है। "
            "हम आपसे तय समय पर contact करेंगे। "
            "धन्यवाद, आपका दिन शुभ हो।"
        ),
        "required_function_call": None,
    }
]


# =============================================================================
# scenario_payment_dispute_verification
# =============================================================================

scenario_payment_dispute_verification = [
    # Turn 0 – User confirms identity
    {
        "input": "हाँ, मैं Chintan बोल रहा हूँ।",
        "golden_text": (
            "नमस्ते Chintan जी, मैं Divya बोल रही हूँ HDFC Bank से। "
            "तो आपके personal loan account — last four digits 6789 — पर 12,000 रुपये का payment 1st March को due था। "
            "आपने 3rd March को pay करने का promise किया था लेकिन अभी तक payment receive नहीं हुई है। क्या आपने payment कर दी है?"
        ),
        "required_function_call": None,
    },
    # Turn 1 – User claims payment done
    {
        "input": "हाँ मैंने payment कर दिया था 3 March को ही।",
        "golden_text": (
            "अच्छा Chintan जी, धन्यवाद बताने के लिए। "
            "क्या आप please payment की date, amount और किस mode से आपने payment किया था वो confirm कर सकते हैं?"
        ),
        "required_function_call": None,
    },
    # Turn 2 – User provides details; agent confirms
    {
        "input": "मैंने 3 March को UPI से पूरे 12000 रुपये pay किए थे।",
        "golden_text": (
            "तो confirm करूँ — आपने 3rd March को UPI से 12,000 रुपये का payment किया है, सही है?"
        ),
        "required_function_call": None,
    },
    # Turn 3 – User confirms; agent records and user gets defensive
    {
        "input": "हाँ बिल्कुल सही है, फिर भी आप लोग बार-बार क्यों call कर रहे हो?",
        "golden_text": (
            "आपकी payment details record कर लेती हूँ... "
            "समझ सकती हूँ Chintan जी, ऐसा होने पर frustration होता है। "
            "कभी-कभी payment reflect होने में 1-3 business days लग सकते हैं, इसलिए cross-check करना जरूरी होता है। "
            "मैं ensure करूँगी कि आपके details verify हो जाएं और unnecessary calls ना आएं।"
        ),
        "required_function_call": {
            "name": "recordPayment",
            "args": {
                "accountNumber": "123456789",
                "paymentDate": "2026-03-03",
                "paymentMode": "upi",
                "amount": 12000
            }
        },
        "function_call_response": {
            "status": "pending_verification"
        }
    },
    # Turn 4 – User insists issue should be resolved
    {
        "input": "देख लीजिए जल्दी, मुझे बार-बार call मत करना।",
        "golden_text": (
            "बिल्कुल Chintan जी, मैं आपकी बात समझती हूँ और इसे priority पर check करवाऊँगी। "
            "आपके payment details verify होने के बाद system update हो जाएगा और calls रुक जाएंगे। "
            "धन्यवाद for your patience, आपका दिन शुभ हो।"
        ),
        "required_function_call": None,
    }
]


# =============================================================================
# scenario_wrong_number_identification
# =============================================================================

scenario_wrong_number_identification = [
    # Turn 0 – Wrong person answers
    {
        "input": "नहीं, यहाँ कोई Chintan नहीं है, आपने गलत नंबर मिलाया है।",
        "golden_text": (
            "अच्छा, माफ़ कीजिएगा disturbance के लिए। "
            "क्या आप confirm कर सकते हैं कि क्या यह number पहले कभी Chintan जी use करते थे या यह completely wrong number है?"
        ),
        "required_function_call": None,
    },
    # Turn 1 – User confirms wrong number
    {
        "input": "नहीं, मैं इस number को पिछले 5 साल से use कर रहा हूँ, मुझे नहीं पता Chintan कौन है।",
        "golden_text": (
            "समझ गई, धन्यवाद clarification के लिए। "
            "मैं इस number को update करवा दूँगी ताकि आगे आपको इस तरह के calls ना आएं। "
            "Sorry for the inconvenience, आपका दिन शुभ हो।"
        ),
        "required_function_call": None,
    }
]


# =============================================================================
# scenario_customer_deceased
# =============================================================================

scenario_customer_deceased = [
    # Turn 0 – Someone else answers and informs customer is deceased
    {
        "input": "Chintan अब इस दुनिया में नहीं है, उनका पिछले महीने निधन हो गया।",
        "golden_text": (
            "ओह... मुझे ये सुनकर बहुत दुख हुआ। "
            "मैं sincerely आपकी situation समझ सकती हूँ और इस कठिन समय में आपको disturb करने के लिए माफ़ी चाहती हूँ। "
            "क्या आप बता सकते हैं कि आप उनसे किस relation में हैं?"
        ),
        "required_function_call": None,
    },
    # Turn 1 – Relative responds
    {
        "input": "मैं उनका भाई बोल रहा हूँ।",
        "golden_text": (
            "समझ गई, और एक बार फिर से मेरी संवेदनाएँ आपके साथ हैं। "
            "मैं इस information को अपने system में update करवा दूँगी ताकि आगे कोई calls ना आएं। "
            "क्या आप confirm कर सकते हैं कि उनका निधन किस तारीख को हुआ था?"
        ),
        "required_function_call": None,
    },
    # Turn 2 – Relative provides date
    {
        "input": "15 February को हुआ था।",
        "golden_text": (
            "ठीक है, धन्यवाद ये details share करने के लिए। "
            "मैं ensure करूँगी कि हमारे records update हो जाएं और future में आपको इस बारे में disturb ना किया जाए। "
            "इस कठिन समय में हम आपकी privacy का पूरा ध्यान रखेंगे।"
        ),
        "required_function_call": None,
    },
    # Turn 3 – Call closing
    {
        "input": "ठीक है।",
        "golden_text": (
            "धन्यवाद आपकी cooperation के लिए। "
            "हम आगे से ध्यान रखेंगे कि आपको इस मामले में कोई inconvenience ना हो। "
            "आपका दिन शांतिपूर्ण रहे।"
        ),
        "required_function_call": None,
    }
]


# =============================================================================
# scenario_user_questions_authenticity
# =============================================================================

scenario_user_questions_authenticity = [
    # Turn 0 – User questions authenticity
    {
        "input": "आप सच में HDFC से बोल रहे हो? आपको मेरे details कैसे मिले?",
        "golden_text": (
            "अच्छा Chintan जी, आपका concern बिल्कुल valid है। "
            "मैं Divya बोल रही हूँ HDFC Bank से, और हम सिर्फ आपके loan account से related verified records के basis पर ही contact करते हैं। "
            "आपके personal loan account — last four digits 6789 — पर 12,000 रुपये का payment 1st March को due था, क्या आपने payment कर दी है?"
        ),
        "required_function_call": None,
    },
    # Turn 1 – User still doubtful
    {
        "input": "मुझे trust नहीं हो रहा, आप proof दे सकते हो?",
        "golden_text": (
            "समझ सकती हूँ Chintan जी, आजकल ऐसे concerns होना common है। "
            "आप चाहें तो HDFC Bank के official customer care number पर call करके भी verify कर सकते हैं। "
            "फिलहाल मैं सिर्फ आपका payment status confirm करना चाह रही थी — क्या आपने payment कर दी है?"
        ),
        "required_function_call": None,
    },
    # Turn 2 – User relaxes and responds
    {
        "input": "ठीक है, payment अभी नहीं किया है।",
        "golden_text": (
            "ठीक है Chintan जी, मैं समझ सकती हूँ। "
            "अभी payment 4 दिन overdue है, लेकिन अभी तक कोई credit impact नहीं हुआ है — हालांकि late fee लग सकती है। "
            "आप कब तक payment कर पाएंगे?"
        ),
        "required_function_call": None,
    },
    # Turn 3 – User commits to pay; agent confirms details
    {
        "input": "मैं 10 March को पूरा payment कर दूंगा, online करूँगा।",
        "golden_text": (
            "तो confirm करूँ — आप 12,000 रुपये 10th March को online pay करेंगे। सही है?"
        ),
        "required_function_call": None,
    },
    # Turn 4 – User confirms; agent triggers tool and closes
    {
        "input": "हाँ सही है।",
        "golden_text": (
            "आपकी payment commitment set up कर देती हूँ... "
            "ठीक है Chintan जी, आपका payment commitment note कर लिया गया है। "
            "कृपया ensure करें कि payment time पर हो जाए ताकि आगे charges avoid हो सकें। "
            "धन्यवाद, आपका दिन शुभ हो।"
        ),
        "required_function_call": {
            "name": "createPromiseToPay",
            "args": {
                "accountNumber": "123456789",
                "promiseDate": "2026-03-10",
                "promiseAmount": 12000,
                "paymentMode": "online"
            }
        },
        "function_call_response": {
            "status": "success"
        }
    }
]


# =============================================================================
# scenario_user_agrees_immediate_payment
# =============================================================================

scenario_user_agrees_immediate_payment = [
    # Turn 0 – User confirms identity
    {
        "input": "हाँ, मैं Chintan बोल रहा हूँ।",
        "golden_text": (
            "नमस्ते Chintan जी, मैं Divya बोल रही हूँ HDFC Bank से। "
            "तो आपके personal loan account — last four digits 6789 — पर 12,000 रुपये का payment 1st March को due था। "
            "आपने 3rd March को pay करने का promise किया था लेकिन अभी तक payment receive नहीं हुई है। क्या आपने payment कर दी है?"
        ),
        "required_function_call": None,
    },
    # Turn 1 – User apologizes and acknowledges delay
    {
        "input": "नहीं, sorry मैं payment करना भूल गया था, मेरी गलती है।",
        "golden_text": (
            "कोई बात नहीं Chintan जी, ऐसा कभी-कभी हो जाता है। "
            "अभी payment 4 दिन overdue है, लेकिन अभी तक कोई credit impact नहीं हुआ है — हालांकि late fee लग सकती है। "
            "क्या आप अभी payment कर पाएंगे?"
        ),
        "required_function_call": None,
    },
    # Turn 2 – User agrees to pay immediately; agent confirms details
    {
        "input": "हाँ, मैं अभी तुरंत पूरे 12000 का payment कर देता हूँ UPI से।",
        "golden_text": (
            "तो confirm करूँ — आप 12,000 रुपये आज, 7th March को UPI से pay कर रहे हैं। सही है?"
        ),
        "required_function_call": None,
    },
    # Turn 3 – User confirms; agent triggers tool and closes
    {
        "input": "हाँ, अभी कर रहा हूँ।",
        "golden_text": (
            "आपकी payment commitment set up कर देती हूँ... "
            "ठीक है Chintan जी, धन्यवाद for your prompt action। "
            "कृपया ensure करें कि payment successful हो जाए, और 1-3 business days में system में reflect हो जाएगा। "
            "धन्यवाद, आपका दिन शुभ हो।"
        ),
        "required_function_call": {
            "name": "createPromiseToPay",
            "args": {
                "accountNumber": "123456789",
                "promiseDate": "2026-03-07",
                "promiseAmount": 12000,
                "paymentMode": "upi"
            }
        },
        "function_call_response": {
            "status": "success"
        }
    }
]


# =============================================================================
# scenario_customer_disputes_amount_and_penalties
# =============================================================================

scenario_customer_disputes_amount_and_penalties = [
    # Turn 0 – User confirms identity
    {
        "input": "हाँ, मैं Chintan बोल रहा हूँ।",
        "golden_text": (
            "नमस्ते Chintan जी, मैं Divya बोल रही हूँ HDFC Bank से। "
            "तो आपके personal loan account — last four digits 6789 — पर 12,000 रुपये का payment 1st March को due था। "
            "आपने 3rd March को pay करने का promise किया था लेकिन अभी तक payment receive नहीं हुई है। क्या आपने payment कर दी है?"
        ),
        "required_function_call": None,
    },
    # Turn 1 – User disputes amount and penalties
    {
        "input": "ये amount गलत है, इतना नहीं बनता और आप लोग extra charges लगा रहे हो।",
        "golden_text": (
            "अच्छा Chintan जी, मैं आपकी concern समझ सकती हूँ। "
            "current outstanding में due amount और applicable charges शामिल होते हैं, लेकिन मैं आपकी बात note कर रही हूँ। "
            "फिलहाल क्या आपने कोई payment already किया है?"
        ),
        "required_function_call": None,
    },
    # Turn 2 – User insists it's incorrect and refuses to pay
    {
        "input": "नहीं, और जब तक सही amount नहीं बताओगे मैं payment नहीं करूँगा।",
        "golden_text": (
            "ठीक है Chintan जी, आपकी बात समझ में आती है। "
            "मैं आपको अपने colleague से connect कर देती हूँ जो amount details verify करके "
            "आपकी concern resolve कर सकते हैं..."
        ),
        "required_function_call": {
            "name": "transferCall",
            "args": {
                "accountNumber": "123456789",
                "reason": "settlement_request"
            }
        },
        "function_call_response": {
            "status": "transferred"
        }
    }
]


# =============================================================================
# scenario_payment_failed_insufficient_funds
# =============================================================================

scenario_payment_failed_insufficient_funds = [
    # Turn 0 – User confirms identity
    {
        "input": "हाँ, मैं Chintan बोल रहा हूँ।",
        "golden_text": (
            "नमस्ते Chintan जी, मैं Divya बोल रही हूँ HDFC Bank से। "
            "तो आपके personal loan account — last four digits 6789 — पर 12,000 रुपये का payment 1st March को due था। "
            "आपने 3rd March को pay करने का promise किया था लेकिन अभी तक payment receive नहीं हुई है। क्या आपने payment कर दी है?"
        ),
        "required_function_call": None,
    },
    # Turn 1 – User says payment failed
    {
        "input": "मैंने try किया था payment करने का लेकिन fail हो गया, account में balance नहीं था।",
        "golden_text": (
            "अच्छा Chintan जी, समझ सकती हूँ — कभी-कभी insufficient balance की वजह से ऐसा हो जाता है। "
            "अभी payment 4 दिन overdue है, लेकिन अभी तक कोई credit impact नहीं हुआ है — हालांकि late fee लग सकती है। "
            "क्या आप alternate mode से आज payment arrange कर पाएंगे?"
        ),
        "required_function_call": None,
    },
    # Turn 2 – User agrees to partial immediate payment; agent confirms
    {
        "input": "अभी मेरे पास 5000 हैं, UPI से दे देता हूँ, बाकी बाद में दे दूंगा।",
        "golden_text": (
            "ठीक है Chintan जी, partial payment भी helpful रहेगा। "
            "तो confirm करूँ — आप 5,000 रुपये आज, 7th March को UPI से pay करेंगे। सही है?"
        ),
        "required_function_call": None,
    },
    # Turn 3 – User confirms first payment; provides second commitment
    {
        "input": "हाँ, और बाकी 7000 मैं 15 March को UPI से ही दे दूंगा।",
        "golden_text": (
            "आपकी payment commitment set up कर देती हूँ... "
            "तो confirm करूँ — आप बाकी 7,000 रुपये 15th March को UPI से pay करेंगे। सही है?"
        ),
        "required_function_call": {
            "name": "createPromiseToPay",
            "args": {
                "accountNumber": "123456789",
                "promiseDate": "2026-03-07",
                "promiseAmount": 5000,
                "paymentMode": "upi"
            }
        },
        "function_call_response": {
            "status": "success"
        }
    },
    # Turn 4 – User confirms second; agent triggers second tool and closes
    {
        "input": "हाँ सही है।",
        "golden_text": (
            "आपकी दूसरी payment commitment भी set up कर देती हूँ... "
            "ठीक है Chintan जी, आपका दोनों payments का commitment note कर लिया गया है। "
            "कृपया ensure करें कि payments time पर हो जाएं ताकि आगे charges avoid हो सकें। "
            "धन्यवाद, आपका दिन शुभ हो।"
        ),
        "required_function_call": {
            "name": "createPromiseToPay",
            "args": {
                "accountNumber": "123456789",
                "promiseDate": "2026-03-15",
                "promiseAmount": 7000,
                "paymentMode": "upi"
            }
        },
        "function_call_response": {
            "status": "success"
        }
    }
]


# =============================================================================
# scenario_payment_channel_issue_app_not_working
# =============================================================================

scenario_payment_channel_issue_app_not_working = [
    # Turn 0 – User confirms identity
    {
        "input": "हाँ, मैं Chintan बोल रहा हूँ।",
        "golden_text": (
            "नमस्ते Chintan जी, मैं Divya बोल रही हूँ HDFC Bank से। "
            "तो आपके personal loan account — last four digits 6789 — पर 12,000 रुपये का payment 1st March को due था। "
            "आपने 3rd March को pay करने का promise किया था लेकिन अभी तक payment receive नहीं हुई है। क्या आपने payment कर दी है?"
        ),
        "required_function_call": None,
    },
    # Turn 1 – User says app/website not working
    {
        "input": "मैंने try किया था app से payment करने का, लेकिन app ही काम नहीं कर रहा था।",
        "golden_text": (
            "अच्छा Chintan जी, समझ सकती हूँ — कभी-कभी technical issues की वजह से ऐसा हो जाता है। "
            "अभी payment 4 दिन overdue है, लेकिन अभी तक कोई credit impact नहीं हुआ है — हालांकि late fee लग सकती है। "
            "क्या आप alternate mode जैसे UPI या net banking से payment कर पाएंगे?"
        ),
        "required_function_call": None,
    },
    # Turn 2 – User says no payment link received
    {
        "input": "मुझे कोई payment link भी नहीं मिला है अभी तक।",
        "golden_text": (
            "ठीक है Chintan जी, मैं आपकी बात समझ रही हूँ। "
            "आप अपने registered bank app या UPI से directly payment कर सकते हैं using your loan details। "
            "क्या आप आज payment करने की कोशिश कर पाएंगे?"
        ),
        "required_function_call": None,
    },
    # Turn 3 – User agrees to pay later; agent confirms
    {
        "input": "आज नहीं हो पाएगा, मैं कल 8 March को पूरे 12000 UPI से try करूँगा।",
        "golden_text": (
            "ठीक है Chintan जी। "
            "तो confirm करूँ — आप 12,000 रुपये 8th March को UPI से pay करेंगे। सही है?"
        ),
        "required_function_call": None,
    },
    # Turn 4 – User confirms; agent triggers tool and closes
    {
        "input": "हाँ, कल कर दूंगा।",
        "golden_text": (
            "आपकी payment commitment set up कर देती हूँ... "
            "ठीक है Chintan जी, आपका payment commitment note कर लिया गया है। "
            "कृपया ensure करें कि payment time पर हो जाए ताकि आगे charges avoid हो सकें। "
            "धन्यवाद, आपका दिन शुभ हो।"
        ),
        "required_function_call": {
            "name": "createPromiseToPay",
            "args": {
                "accountNumber": "123456789",
                "promiseDate": "2026-03-08",
                "promiseAmount": 12000,
                "paymentMode": "upi"
            }
        },
        "function_call_response": {
            "status": "success"
        }
    }
]


# =============================================================================
# scenario_X_multiple_missed_emis_escalation
# =============================================================================

scenario_X_multiple_missed_emis_escalation = [
    {
        "input": "हाँ, मैं Chintan बोल रहा हूँ।",
        "golden_text": (
            "नमस्ते Chintan जी, मैं Divya बोल रही हूँ HDFC Bank से। "
            "तो… आपके personal loan account — last four digits six seven eight nine — पर twelve thousand rupees का payment 1st March को due था। "
            "आपने 3rd March का promise भी miss कर दिया है, क्या आपने payment कर दी है?"
        ),
        "required_function_call": None,
    },
    {
        "input": "नहीं, अभी नहीं किया। पिछले महीने भी नहीं कर पाया था।",
        "golden_text": (
            "अच्छा… Chintan जी, मैं समझ सकती हूँ लेकिन लगातार payments miss होने से concern बढ़ जाता है। "
            "अभी 6 दिन overdue है इसलिए credit impact नहीं हुआ है, लेकिन late fees और आगे risk बढ़ सकता है। "
            "आप बता सकते हैं कि अभी payment क्यों नहीं हो पा रही है?"
        ),
        "required_function_call": None,
    },
    {
        "input": "मेरी job चली गई है, अभी पैसे arrange करना मुश्किल है।",
        "golden_text": (
            "मुझे समझ आ रहा है Chintan जी, ये situation tough होती है। "
            "लेकिन loan obligations continue रहते हैं, इसलिए हमें कोई solution निकालना पड़ेगा। "
            "क्या आप थोड़ा amount arrange करके कोई payment commitment दे सकते हैं?"
        ),
        "required_function_call": None,
    },
    {
        "input": "नहीं, अभी तो कुछ भी नहीं दे सकता। कोई settlement type option हो तो बताइए।",
        "golden_text": (
            "ठीक है Chintan जी, settlement ke liye mujhe aapko humare team se connect karna hoga "
            "jo aapko better guide kar sakenge..."
        ),
        "required_function_call": {
            "name": "transferCall",
            "args": {
                "accountNumber": "123456789",
                "reason": "settlement_request"
            }
        },
        "function_call_response": {
            "status": "transferred"
        }
    }
]


# =============================================================================
# scenario_X_final_warning_before_legal_escalation
# =============================================================================

scenario_X_final_warning_before_legal_escalation = [
    {
        "input": "जी, मैं Chintan बोल रहा हूँ।",
        "golden_text": (
            "नमस्ते Chintan जी, मैं Divya बोल रही हूँ HDFC Bank से। "
            "तो… आपके personal loan account — last four digits six seven eight nine — पर twelve thousand rupees का payment 1st March को due था। "
            "आपने 3rd March का promise भी miss कर दिया है, क्या आपने payment कर दी है?"
        ),
        "required_function_call": None,
    },
    {
        "input": "नहीं, अभी तक नहीं किया।",
        "golden_text": (
            "अच्छा… Chintan जी, मैं समझ सकती हूँ लेकिन अब ये payment 4 दिन overdue हो चुका है। "
            "अभी तक credit impact नहीं हुआ है, लेकिन late fee लग रही है और आगे action लिया जा सकता है। "
            "आप बता सकते हैं कि payment क्यों नहीं हो पाया?"
        ),
        "required_function_call": None,
    },
    {
        "input": "बस delay हो गया, अभी पैसे arrange नहीं हुए।",
        "golden_text": (
            "समझ रही हूँ Chintan जी, लेकिन ये already आपका previous promise भी miss हो चुका है। "
            "अगर payment और delay होता है, तो bank को formal recovery process initiate करना पड़ सकता है। "
            "क्या आप आज या कल तक कोई payment कर सकते हैं?"
        ),
        "required_function_call": None,
    },
    {
        "input": "नहीं, अभी तुरंत possible नहीं है।",
        "golden_text": (
            "देखिए Chintan जी, ये final reminder के तौर पर call किया जा रहा है। "
            "अगर payment नहीं आता है, तो आगे legal escalation या field visit initiate हो सकता है। "
            "फिर भी, क्या आप कोई निश्चित date बता सकते हैं जब आप payment कर पाएंगे?"
        ),
        "required_function_call": None,
    },
    {
        "input": "ठीक है, मैं 2-3 दिन में arrange कर लूंगा।",
        "golden_text": (
            "अच्छा… please exact date confirm कर दीजिए ताकि मैं इसे properly note कर सकूँ। "
            "कितने amount का payment करेंगे और किस mode से करेंगे?"
        ),
        "required_function_call": None,
    },
    {
        "input": "पूरा 12000, UPI से 10 मार्च तक कर दूंगा।",
        "golden_text": (
            "तो confirm करूँ — आप twelve thousand rupees, 10th March को UPI से pay करेंगे। सही है?"
        ),
        "required_function_call": None,
    },
    {
        "input": "हाँ, सही है।",
        "golden_text": (
            "आपकी payment commitment set up कर देती हूँ... "
            "ठीक है Chintan जी, आपका payment commitment successfully record हो गया है। "
            "कृपया 10th March तक payment कर दीजिए ताकि आगे कोई escalation ना हो। "
            "धन्यवाद, आपका दिन शुभ रहे।"
        ),
        "required_function_call": {
            "name": "createPromiseToPay",
            "args": {
                "accountNumber": "123456789",
                "promiseDate": "2026-03-10",
                "promiseAmount": 12000,
                "paymentMode": "upi"
            }
        },
        "function_call_response": {
            "status": "success"
        }
    }
]


# =============================================================================
# scenario_X_salary_not_credited_delay
# =============================================================================

scenario_X_salary_not_credited_delay = [
    {
        "input": "हाँ, मैं Chintan बोल रहा हूँ।",
        "golden_text": (
            "नमस्ते Chintan जी, मैं Divya बोल रही हूँ HDFC Bank से। "
            "तो… आपके personal loan account — last four digits six seven eight nine — पर twelve thousand rupees का payment 1st March को due था। "
            "आपने 3rd March का promise भी miss कर दिया है, क्या आपने payment कर दी है?"
        ),
        "required_function_call": None,
    },
    {
        "input": "नहीं, अभी नहीं किया। salary अभी तक credit नहीं हुई है।",
        "golden_text": (
            "अच्छा… समझ सकती हूँ Chintan जी, salary delay होने से problem हो जाती है। "
            "अभी payment 4 दिन overdue है, credit impact तो नहीं हुआ है लेकिन late fee लग सकती है। "
            "आपको कब तक salary credit होने की उम्मीद है?"
        ),
        "required_function_call": None,
    },
    {
        "input": "शायद 2-3 दिन में आ जाएगी।",
        "golden_text": (
            "ठीक है… जैसे ही salary credit हो जाए, आप payment कर सकते हैं। "
            "बस confirm कर दीजिए कि आप कितने amount और किस date तक pay कर पाएंगे।"
        ),
        "required_function_call": None,
    },
    {
        "input": "पूरा amount 12000, 10 मार्च तक कर दूंगा UPI से।",
        "golden_text": (
            "तो confirm करूँ — आप twelve thousand rupees, 10th March को UPI से pay करेंगे। सही है?"
        ),
        "required_function_call": None,
    },
    {
        "input": "हाँ, सही है।",
        "golden_text": (
            "आपकी payment commitment set up कर देती हूँ... "
            "ठीक है Chintan जी, आपका payment commitment successfully record हो गया है। "
            "कृपया 10th March तक payment कर दीजिए ताकि late charges आगे ना बढ़ें। "
            "धन्यवाद, आपका दिन शुभ रहे।"
        ),
        "required_function_call": {
            "name": "createPromiseToPay",
            "args": {
                "accountNumber": "123456789",
                "promiseDate": "2026-03-10",
                "promiseAmount": 12000,
                "paymentMode": "upi"
            }
        },
        "function_call_response": {
            "status": "success"
        }
    }
]


# =============================================================================
# scenario_X_technical_glitch_payment_failure
# =============================================================================

scenario_X_technical_glitch_payment_failure = [
    {
        "input": "हाँ, मैं Chintan बोल रहा हूँ।",
        "golden_text": (
            "नमस्ते Chintan जी, मैं Divya बोल रही हूँ HDFC Bank से। "
            "तो… आपके personal loan account — last four digits six seven eight nine — पर twelve thousand rupees का payment 1st March को due था। "
            "आपने 3rd March का promise भी miss कर दिया है, क्या आपने payment कर दी है?"
        ),
        "required_function_call": None,
    },
    {
        "input": "मैंने try किया था, लेकिन app में error आ रहा था, payment नहीं हुआ।",
        "golden_text": (
            "अच्छा… Chintan जी, समझ सकती हूँ कि technical issue की वजह से payment नहीं हो पाया। "
            "अभी payment 4 दिन overdue है, credit impact नहीं हुआ है लेकिन late fee लग सकती है। "
            "क्या आपने दुबारा payment करने की कोशिश की?"
        ),
        "required_function_call": None,
    },
    {
        "input": "नहीं, उसके बाद try नहीं किया।",
        "golden_text": (
            "ठीक है… मैं suggest करूँगी कि आप फिर से try करें, या alternate method जैसे UPI या net banking use कर सकते हैं। "
            "ताकि और delay ना हो, आप कब तक payment कर पाएंगे?"
        ),
        "required_function_call": None,
    },
    {
        "input": "आज शाम तक पूरा 12000 कर दूंगा UPI से।",
        "golden_text": (
            "तो confirm करूँ — आप twelve thousand rupees, 7th March को UPI से pay करेंगे। सही है?"
        ),
        "required_function_call": None,
    },
    {
        "input": "हाँ, सही है।",
        "golden_text": (
            "आपकी payment commitment set up कर देती हूँ... "
            "ठीक है Chintan जी, आपका payment commitment successfully record हो गया है। "
            "कृपया आज ही payment complete कर दीजिए ताकि further charges avoid हो सकें। "
            "धन्यवाद, आपका दिन शुभ रहे।"
        ),
        "required_function_call": {
            "name": "createPromiseToPay",
            "args": {
                "accountNumber": "123456789",
                "promiseDate": "2026-03-07",
                "promiseAmount": 12000,
                "paymentMode": "upi"
            }
        },
        "function_call_response": {
            "status": "success"
        }
    }
]


# =============================================================================
# scenario_X_payment_deducted_but_status_failed
# =============================================================================

scenario_X_payment_deducted_but_status_failed = [
    {
        "input": "हाँ, मैं Chintan बोल रहा हूँ।",
        "golden_text": (
            "तो Chintan जी, मैं Divya बोल रही हूँ HDFC Bank से। "
            "आपके personal loan account — last four digits six seven eight nine — पर twelve thousand rupees का payment 1st March को due था। "
            "आपने 3rd March को pay करने का promise किया था लेकिन payment अभी तक नहीं दिख रहा है। क्या आपने payment की है?"
        ),
        "required_function_call": None,
    },
    {
        "input": "हाँ मैंने payment किया था, लेकिन app में failed दिखा रहा है, पर पैसे कट गए हैं।",
        "golden_text": (
            "अच्छा, समझ गई Chintan जी — कभी-कभी technical issue की वजह से ऐसा हो जाता है। "
            "आप please payment की date, amount और किस mode से किया था वो confirm कर दीजिए, ताकि मैं check कर सकूँ।"
        ),
        "required_function_call": None,
    },
    {
        "input": "5 March को UPI से 12000 रुपये किया था।",
        "golden_text": (
            "तो confirm करूँ — आपने 5th March को UPI से twelve thousand rupees pay किया है। सही है?"
        ),
        "required_function_call": None,
    },
    {
        "input": "हाँ, सही है।",
        "golden_text": (
            "आपकी payment details record कर लेती हूँ... "
            "आपकी payment details record हो गई हैं। "
            "ये details 1–3 working days में reflect हो जानी चाहिए।"
        ),
        "required_function_call": {
            "name": "recordPayment",
            "args": {
                "accountNumber": "123456789",
                "paymentDate": "2026-03-05",
                "paymentMode": "upi",
                "amount": 12000
            }
        },
        "function_call_response": {"status": "success"}
    },
    {
        "input": "अगर reflect नहीं हुआ तो क्या होगा?",
        "golden_text": (
            "तो Chintan जी, अगर 2–3 working days में reflect नहीं होता है, तो आप bank statement या transaction ID share कर सकते हैं। "
            "हमारी team उसे verify करके update कर देगी। "
            "आप tension मत लीजिए, मैं note कर चुकी हूँ।"
        ),
        "required_function_call": None,
    },
    {
        "input": "ठीक है, मैं wait करता हूँ।",
        "golden_text": (
            "ठीक है Chintan जी, धन्यवाद for your time। "
            "आपका payment update जल्द reflect हो जाना चाहिए, और किसी भी issue में आप support से contact कर सकते हैं। "
            "Have a good day!"
        ),
        "required_function_call": None,
    }
]


# =============================================================================
# scenario_X_app_crash_during_payment
# =============================================================================

scenario_X_app_crash_during_payment = [
    {
        "input": "हाँ, मैं Chintan बोल रहा हूँ।",
        "golden_text": (
            "तो Chintan जी, मैं Divya बोल रही हूँ HDFC Bank से। "
            "आपके personal loan account — last four digits six seven eight nine — पर twelve thousand rupees का payment 1st March को due था। "
            "आपने 3rd March को pay करने का promise किया था लेकिन payment अभी तक नहीं दिख रहा है। क्या आपने payment की है?"
        ),
        "required_function_call": None,
    },
    {
        "input": "मैं payment करने गया था, लेकिन app freeze हो गया और crash हो गया।",
        "golden_text": (
            "अच्छा, समझ गई Chintan जी — कभी-कभी app issue की वजह से ऐसा हो सकता है। "
            "लेकिन अभी payment pending है और 4 दिन overdue हो चुका है, हालांकि अभी credit impact नहीं है पर late fee लग सकती है। "
            "क्या आप अभी किसी alternate mode से payment कर सकते हैं?"
        ),
        "required_function_call": None,
    },
    {
        "input": "अभी नहीं कर सकता, थोड़ा time लगेगा arrange करने में।",
        "golden_text": (
            "ठीक है Chintan जी, मैं समझ सकती हूँ — कभी-कभी arrangement में समय लग जाता है। "
            "आप please बताइए कि आप कब तक payment कर पाएंगे, ताकि मैं accordingly note कर सकूँ।"
        ),
        "required_function_call": None,
    },
    {
        "input": "10 March तक कर दूंगा, online ही करूँगा।",
        "golden_text": (
            "तो confirm करूँ — आप twelve thousand rupees, 10th March को online mode से pay करेंगे। सही है?"
        ),
        "required_function_call": None,
    },
    {
        "input": "हाँ सही है।",
        "golden_text": (
            "आपकी payment commitment set up कर देती हूँ... "
            "ठीक है Chintan जी, धन्यवाद for confirming। "
            "कृपया ensure कर लीजिए कि payment 10th March तक हो जाए ताकि आगे कोई charges न लगे। "
            "Have a good day!"
        ),
        "required_function_call": {
            "name": "createPromiseToPay",
            "args": {
                "accountNumber": "123456789",
                "promiseDate": "2026-03-10",
                "promiseAmount": 12000,
                "paymentMode": "online"
            }
        },
        "function_call_response": {"status": "success"}
    }
]


# =============================================================================
# scenario_X_otp_not_received
# =============================================================================

scenario_X_otp_not_received = [
    {
        "input": "जी, मैं Chintan हूँ।",
        "golden_text": (
            "तो Chintan जी, मैं Divya बोल रही हूँ HDFC Bank से। "
            "आपके personal loan account — last four digits six seven eight nine — पर twelve thousand rupees का payment 1st March को due था। "
            "आपने 3rd March को pay करने का promise किया था लेकिन payment अभी तक नहीं आया है। क्या आपने payment की है?"
        ),
        "required_function_call": None,
    },
    {
        "input": "मैं payment कर रहा था लेकिन OTP ही नहीं आया, इसलिए नहीं हो पाया।",
        "golden_text": (
            "अच्छा, समझ गई Chintan जी — कभी-कभी OTP delay या network issue की वजह से ऐसा हो जाता है। "
            "लेकिन अभी payment pending है और 4 दिन overdue हो चुका है, अभी credit impact नहीं है पर late fee लग सकती है। "
            "क्या आप थोड़ी देर बाद फिर से try कर सकते हैं या किसी दूसरे mode से payment कर सकते हैं?"
        ),
        "required_function_call": None,
    },
    {
        "input": "अभी busy हूँ, बाद में try करूँगा।",
        "golden_text": (
            "ठीक है Chintan जी, मैं समझ सकती हूँ — अभी आप busy होंगे। "
            "आप please बताइए कि कब तक आप payment कर पाएंगे, ताकि मैं एक commitment note कर सकूँ।"
        ),
        "required_function_call": None,
    },
    {
        "input": "आज शाम तक पूरे 12000 UPI से pay करने का try करूँगा, अगर OTP आया तो कर दूँगा।",
        "golden_text": (
            "तो confirm करूँ — आप twelve thousand rupees आज, 7th March को UPI से payment करने की कोशिश करेंगे। सही है?"
        ),
        "required_function_call": None,
    },
    {
        "input": "हाँ सही है।",
        "golden_text": (
            "आपकी payment commitment set up कर देती हूँ... "
            "ठीक है Chintan जी, धन्यवाद for confirming। "
            "कृपया ensure कर लीजिए कि आज payment complete हो जाए ताकि late charges avoid हो सके। "
            "Have a good day!"
        ),
        "required_function_call": {
            "name": "createPromiseToPay",
            "args": {
                "accountNumber": "123456789",
                "promiseDate": "2026-03-07",
                "promiseAmount": 12000,
                "paymentMode": "upi"
            }
        },
        "function_call_response": {"status": "success"}
    }
]


# =============================================================================
# scenario_X_auto_debit_failed
# =============================================================================

scenario_X_auto_debit_failed = [
    {
        "input": "हाँ, मैं Chintan बोल रहा हूँ।",
        "golden_text": (
            "तो Chintan जी, मैं Divya बोल रही हूँ HDFC Bank से। "
            "आपके personal loan account — last four digits six seven eight nine — पर twelve thousand rupees का payment 1st March को due था। "
            "आपने 3rd March को pay करने का promise किया था लेकिन payment अभी तक receive नहीं हुआ है। क्या आपने payment की है?"
        ),
        "required_function_call": None,
    },
    {
        "input": "मेरे account से तो auto debit होना था, लेकिन हुआ ही नहीं।",
        "golden_text": (
            "अच्छा, समझ गई Chintan जी — कभी-कभी auto-debit mandate issue या insufficient balance की वजह से payment process नहीं हो पाता। "
            "अभी payment pending है और 4 दिन overdue हो चुका है, हालांकि अभी credit impact नहीं है लेकिन late fee लग सकती है। "
            "क्या आप आज manual payment कर सकते हैं?"
        ),
        "required_function_call": None,
    },
    {
        "input": "अभी नहीं कर पाऊंगा, कल salary आएगी तब करूँगा।",
        "golden_text": (
            "ठीक है Chintan जी, समझ सकती हूँ — salary आने का wait करना पड़ता है। "
            "आप please confirm कर दीजिए कि कल किस time तक आप payment कर पाएंगे, ताकि मैं commitment note कर सकूँ।"
        ),
        "required_function_call": None,
    },
    {
        "input": "कल दोपहर तक पूरे 12000 कर दूंगा, UPI से करूँगा।",
        "golden_text": (
            "तो confirm करूँ — आप twelve thousand rupees, 8th March को UPI से pay करेंगे। सही है?"
        ),
        "required_function_call": None,
    },
    {
        "input": "हाँ सही है।",
        "golden_text": (
            "आपकी payment commitment set up कर देती हूँ... "
            "ठीक है Chintan जी, धन्यवाद for confirming। "
            "कृपया ensure कर लीजिए कि payment 8th March तक complete हो जाए ताकि additional charges avoid हो सके। "
            "Have a good day!"
        ),
        "required_function_call": {
            "name": "createPromiseToPay",
            "args": {
                "accountNumber": "123456789",
                "promiseDate": "2026-03-08",
                "promiseAmount": 12000,
                "paymentMode": "upi"
            }
        },
        "function_call_response": {"status": "success"}
    }
]


# =============================================================================
# scenario_account_mismatch_issue
# =============================================================================

scenario_account_mismatch_issue = [
    {
        "input": "हाँ, मैं Chintan बोल रहा हूँ।",
        "golden_text": (
            "तो Chintan जी, मैं Divya बोल रही हूँ HDFC Bank से। "
            "आपके personal loan account — last four digits six seven eight nine — पर twelve thousand rupees का payment 1st March को due था। "
            "आपने 3rd March को pay करने का promise किया था लेकिन payment अभी तक नहीं आयी। क्या आपने payment की है?"
        ),
        "required_function_call": None,
    },
    {
        "input": "नहीं, मैंने try किया था लेकिन account details mismatch दिखा रहा था।",
        "golden_text": (
            "अच्छा, समझ गई Chintan जी — ऐसा कभी-कभी technical issue की वजह से हो जाता है। "
            "फिलहाल payment अभी तक receive नहीं हुआ है, और ये 4 दिन overdue है — अभी credit impact नहीं है लेकिन late fee लग सकती है। "
            "क्या आप आज या कल तक payment retry कर पाएंगे?"
        ),
        "required_function_call": None,
    },
    {
        "input": "अभी तो नहीं कर पाऊंगा, पहले issue resolve करना पड़ेगा।",
        "golden_text": (
            "ठीक है Chintan जी, समझ सकती हूँ कि पहले issue resolve करना ज़रूरी है। "
            "तो आप कब तक expect कर रहे हैं कि ये issue resolve हो जाएगा और आप payment कर पाएंगे?"
        ),
        "required_function_call": None,
    },
    {
        "input": "शायद 2-3 दिन लगेंगे, 10 March को पूरे 12000 कर दूंगा payment, bank transfer से।",
        "golden_text": (
            "तो confirm कर रही हूँ — आप twelve thousand rupees, 10th March को bank transfer से pay करेंगे। सही है?"
        ),
        "required_function_call": None,
    },
    {
        "input": "हाँ, 10 तारीख तक कर दूंगा।",
        "golden_text": (
            "आपकी payment commitment set up कर देती हूँ... "
            "Alright Chintan जी, मैंने आपकी commitment note कर ली है। "
            "कृपया 10th March तक payment complete कर दीजिए ताकि कोई late charges आगे ना बढ़ें। "
            "धन्यवाद, आपका दिन शुभ हो।"
        ),
        "required_function_call": {
            "name": "createPromiseToPay",
            "args": {
                "accountNumber": "123456789",
                "promiseDate": "2026-03-10",
                "promiseAmount": 12000,
                "paymentMode": "bank_transfer"
            }
        },
        "function_call_response": {"status": "success"}
    }
]

turns = (
    # scenario_1_payment_done
     scenario_2_promise_to_pay
    # + scenario_3_settlement
    # + scenario_4_callback
    # + scenario_family_emergency_extension_request
    # + scenario_user_not_available_requests_callback
    # + scenario_payment_dispute_verification
    # + scenario_wrong_number_identification
    # + scenario_customer_deceased
    # + scenario_user_questions_authenticity
    # + scenario_user_agrees_immediate_payment
    # + scenario_customer_disputes_amount_and_penalties
    # + scenario_payment_failed_insufficient_funds
    # + scenario_payment_channel_issue_app_not_working
    # + scenario_X_multiple_missed_emis_escalation
    # + scenario_X_final_warning_before_legal_escalation
    # + scenario_X_salary_not_credited_delay
    # + scenario_X_technical_glitch_payment_failure
    # + scenario_X_payment_deducted_but_status_failed
    # + scenario_X_app_crash_during_payment
    # + scenario_X_otp_not_received
    # + scenario_X_auto_debit_failed
    # + scenario_account_mismatch_issue
)
