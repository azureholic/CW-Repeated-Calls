

output_dict = {'REPEATED_CALL_AGENT':
                                        "Analysis: The current call is about a 'self-driving mower' that isn't working since this morning. The previous call, just one day prior, was about the customer's 'AutoMow 3000' (which is a self-driving mower) that had stopped working. The previous call summary indicates the issue was not resolved immediately and a ticket was opened with a resolution promised by today. The timing is very close (about 1 day apart), and both calls are about the same product and a similar issue (the mower not working). It is highly likely the current call is a follow-up or continuation of the unresolved issue from the previous call. Conclusion: This is a repeated call about the same issue.",
                'CAUSE_AGENT':
                                        "Product ID: 101. Analysis: The customer reported that their self-driving mower stopped working on the morning of January 10, 2024. The customer has an active subscription to the AutoMow 3000 (product ID 101). There were no outages or known bugs reported for this product. However, a major software update was rolled out for this product on January 9, 2024, just one day before the issue was reported. It is likely that the recent software update could have caused the malfunction.. Conclusion: The issue is likely related to the recent major software update for the AutoMow 3000, which was rolled out the day before the problem was reported. This suggests that our system may be responsible for the issue.",
                'DRAFTER': 
                                        "The customer should receive a discount. \
                                            - Offer the 20% discount for 6 months. \
                                            - Reasoning: The customer, Porter Osborne (Customer ID: 7), has a high Customer Lifetime Value (CLV) and is eligible for the highest available discount (20% for 6 months) for the AutoMow 3000 (Product ID: 101). The issue was likely caused by a recent software update, and providing a significant discount is appropriate to maintain goodwill with a valuable customer. \
                                            - The customer reported that their self-driving mower stopped working on the morning of January 10, 2024, possibly due to a software update on January 9, 2024. Please confirm with the customer that the issue began after the update and clarify any additional details about the malfunction. \
                                            - Customer ID: 7, Product ID: 101 \
                                        Please proceed with offering the 20% discount for 6 months and confirm the issue details with the customer. ",
                'REVIEWER':             
                                        "APPROVED \
                                        The offer is relevant to the customer, as they are experiencing an issue with their AutoMow 3000 (Product ID: 101) that likely resulted from a recent software update. The customer, Porter Osborne (Customer ID: 7), has a high CLV and is eligible for the highest available discount (20% for 6 months). The reasoning behind the offer is clear and logical, aiming to maintain goodwill with a valuable customer. The issue and the need to confirm the timing and details with the customer are clearly stated. Both the customer ID and product ID are included. " 
                                                    }



print(output_dict["REVIEWER"])
