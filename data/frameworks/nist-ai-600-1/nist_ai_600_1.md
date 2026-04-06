---
title: "NIST Trustworthy and Responsible AI NIST AI 600-1"
source_file: "NIST.AI.600-1.GenAI-Profile.ipd.pdf"
pages: 64
type: pdf
---

## **NIST Trustworthy and Responsible AI** **NIST AI 600-1**
# **Artificial Intelligence Risk Management** **Framework: Generative Artificial** **Intelligence Profile**

This publication is available free of charge from:

[https://doi.org/10.6028/NIST.AI.600-1](https://doi.org/10.6028/NIST.AI.600-1)


## **NIST Trustworthy and Responsible AI** **NIST AI 600-1**
# **Artificial Intelligence Risk Management** **Framework: Generative Artificial** **Intelligence Profile**

This publication is available free of charge from:

[https://doi.org/10.6028/NIST.AI.600-1](https://doi.org/10.6028/NIST.AI.600-1)


July 2024


U.S. Department of Commerce

_Gina M. Raimondo, Secretary_


National Institute of Standards and Technology
_Laurie E. Locascio, NIST Director and Under Secretary of Commerce for Standards and Technology_


**About AI at NIST** : The National Institute of Standards and Technology (NIST) develops measurements,
technology, tools, and standards to advance reliable, safe, transparent, explainable, privacy-enhanced,
and fair artificial intelligence (AI) so that its full commercial and societal benefits can be realized without
harm to people or the planet. NIST, which has conducted both fundamental and applied work on AI for
more than a decade, is also helping to fulfill the 2023 Executive Order on Safe, Secure, and Trustworthy
AI. NIST established the U.S. AI Safety Institute and the companion AI Safety Institute Consortium to
continue the efforts set in motion by the E.O. to build the science necessary for safe, secure, and
trustworthy development and use of AI.

_**Acknowledgments:**_ _This report was accomplished with the many helpful comments and contributions_
_from the community, including the NIST Generative AI Public Working Group, and NIST staff and guest_
_researchers: Chloe Autio, Jesse Dunietz, Patrick Hall, Shomik Jain, Kamie Roberts, Reva Schwartz, Martin_
_Stanley, and Elham Tabassi._


**NIST Technical Series Policies**
[Copyright, Use, and Licensing Statements](https://doi.org/10.6028/NIST-TECHPUBS.CROSSMARK-POLICY)
[NIST Technical Series Publication Identifier Syntax](https://www.nist.gov/nist-research-library/nist-technical-series-publications-author-instructions#pubid)


**Publication History**
Approved by the NIST Editorial Review Board on 07-25-2024


**Contact Information**
[ai-inquiries@nist.gov](mailto:ai-inquiries@nist.gov)

National Institute of Standards and Technology
Attn: NIST AI Innovation Lab, Information Technology Laboratory
100 Bureau Drive (Mail Stop 8900) Gaithersburg, MD 20899-8900


**Additional Information**
Additional information about this publication and other NIST AI publications are available at
[https://airc.nist.gov/Home.](https://airc.nist.gov/Home)

_Disclaimer_ _**:**_ _Certain commercial entities, equipment, or materials may be identified in this document in_
_order to adequately describe an experimental procedure or concept. Such identification is not intended to_
_imply recommendation or endorsement by the National Institute of Standards and Technology, nor is it_
_intended to imply that the entities, materials, or equipment are necessarily the best available for the_
_purpose. Any mention of commercial, non-profit, academic partners, or their products, or references is_
_for information only; it is not intended to imply endorsement or recommendation by any U.S._
_Government agency._


**Table of Contents**

**1.** **Introduction ..............................................................................................................................................1**

**2.** **Overview of Risks Unique to or Exacerbated by GAI .....................................................................2**


**3.** **Suggested Actions to Manage GAI Risks ......................................................................................... 12**

**Appendix A. Primary GAI Considerations ............................................................................................... 47**

**Appendix B. References ................................................................................................................................ 54**


**1.** **Introduction**


This document is a cross-sectoral profile of and companion resource for the [AI Risk Management](https://www.nist.gov/itl/ai-risk-management-framework)
[Framework](https://www.nist.gov/itl/ai-risk-management-framework) (AI RMF 1.0) for Generative AI, [1] pursuant to President Biden’s Executive Order (EO) 14110 on
Safe, Secure, and Trustworthy Artificial Intelligence. [2] The AI RMF was released in January 2023, and is
intended for voluntary use and to improve the ability of organizations to incorporate trustworthiness
considerations into the design, development, use, and evaluation of AI products, services, and systems.

A _[profle](https://airc.nist.gov/AI_RMF_Knowledge_Base/AI_RMF/Core_And_Profiles/6-sec-profile)_ is an implementation of the AI RMF functions, categories, and subcategories for a specific
setting, application, or technology – in this case, Generative AI (GAI) – based on the requirements, risk
tolerance, and resources of the Framework user. AI RMF profiles assist organizations in deciding how to
best manage AI risks in a manner that is well-aligned with their goals, considers legal/regulatory
requirements and best practices, and reflects risk management priorities. Consistent with other AI RMF
profiles, this profile offers insights into how risk can be managed across various stages of the AI lifecycle
and for GAI as a technology.

As GAI covers risks of models or applications that can be used across use cases or sectors, this document
is an AI RMF cross-sectoral profile. Cross-sectoral profiles can be used to govern, map, measure, and
manage risks associated with activities or business processes common across sectors, such as the use of
large language models (LLMs), cloud-based services, or acquisition.

This document defines risks that are novel to or exacerbated by the use of GAI. After introducing and
describing these risks, the document provides a set of suggested actions to help organizations govern,
map, measure, and manage these risks.


1 EO 14110 defines Generative AI as “the class of AI models that emulate the structure and characteristics of input
data in order to generate derived synthetic content. This can include images, videos, audio, text, and other digital
content.” While not all GAI is derived from foundation models, for purposes of this document, GAI generally refers
to generative foundation models. The foundation model subcategory of “dual-use foundation models” is defined by
EO 14110 as “an AI model that is trained on broad data; generally uses self-supervision; contains at least tens of
billions of parameters; is applicable across a wide range of contexts.”
2 This profile was developed per Section 4.1(a)(i)(A) of EO 14110, which directs the Secretary of Commerce, acting
through the Director of the National Institute of Standards and Technology (NIST), to develop a companion
resource to the AI RMF, NIST AI 100–1, for generative AI.


1


**2.** **Overview of Risks Unique to or Exacerbated by GAI**


In the context of the AI RMF, _risk_ [refers](https://airc.nist.gov/AI_RMF_Knowledge_Base/AI_RMF/Foundational_Information/1-sec-risk) to the composite measure of an event’s **probability** (or
likelihood) of occurring and the **magnitude** or degree of the consequences of the corresponding event.
Some risks can be assessed as likely to materialize in a given context, particularly those that have been
empirically demonstrated in similar contexts. Other risks may be unlikely to materialize in a given
context, or may be more speculative and therefore uncertain.

AI risks can [difer from or intensify traditional software risks. Likewise, GAI can](https://airc.nist.gov/AI_RMF_Knowledge_Base/AI_RMF/Appendices/Appendix_B) [exacerbate](https://www.cyber.gc.ca/en/guidance/generative-artificial-intelligence-ai-itsap00041) existing AI
risks, and creates unique risks. GAI risks can vary along many dimensions:

  - **Stage of the AI lifecycle:** Risks can arise during design, development, deployment, operation,
and/or decommissioning.

  - **Scope:** Risks may exist at individual model or system levels, at the application or implementation
levels (i.e., for a specific use case), or at the ecosystem level – that is, beyond a single system or
organizational context. Examples of the latter include the expansion of “algorithmic
[monocultures,](https://www.pnas.org/doi/10.1073/pnas.2018340118) [3] ” resulting from repeated use of the same model, or impacts on access to
opportunity, [labor markets, and the creative economies.](https://www.nber.org/papers/w32487) [4]

  - **Source of risk:** Risks may emerge from factors related to the design, training, or operation of the
GAI model itself, stemming in some cases from GAI model or system inputs, and in other cases,
from GAI system outputs. Many GAI risks, however, originate from human behavior, including


3 “Algorithmic monocultures” refers to the phenomenon in which repeated use of the same model or algorithm in
consequential decision-making settings like employment and lending can result in increased susceptibility by
systems to correlated failures (like unexpected shocks), due to multiple actors relying on the same algorithm.
4 Many studies have projected the impact of AI on the workforce and labor markets. Fewer studies have examined
the impact of GAI on the labor market, though some industry surveys indicate that that both employees and
employers are pondering this disruption.


2


the abuse, misuse, and unsafe repurposing by humans (adversarial or not), and others result
from interactions between a human and an AI system.

  - **Time** **scale:** GAI risks may materialize abruptly or across extended periods. Examples include
immediate (and/or prolonged) emotional harm and potential risks to physical safety due to the
distribution of harmful deepfake images, or the long-term effect of disinformation on societal
trust in public institutions.

The presence of risks and where they fall along the dimensions above will vary depending on the
characteristics of the GAI model, system, or use case at hand. These characteristics include but are not
limited to GAI model or system architecture, training mechanisms and libraries, data types used for
training or fine-tuning, levels of model access or availability of model weights, and application or use
case context.

Organizations may choose to tailor how they measure GAI risks based on these characteristics. They may
additionally wish to allocate risk management resources relative to the severity and likelihood of
negative impacts, including where and how these risks manifest, and their direct and material impacts
harms in the context of GAI use. Mitigations for model or system level risks may differ from mitigations
for use-case or ecosystem level risks.

Importantly, some GAI risks are unknown, and are therefore difficult to properly scope or evaluate given
the uncertainty about potential GAI scale, complexity, and capabilities. Other risks may be known but
[difcult to estmate](https://arxiv.org/pdf/2011.13416.pdf) given the wide range of GAI stakeholders, uses, inputs, and outputs. Challenges with
risk estimation are aggravated by a lack of visibility into GAI training data, and the generally immature
state of the science of AI measurement and safety today. This document focuses on risks for which there
is an existing empirical evidence base at the time this profile was written; for example, speculative risks
that may potentially arise in more advanced, future GAI systems are not considered. Future updates may
incorporate additional risks or provide further details on the risks identified below.

To guide organizations in identifying and managing GAI risks, a set of risks unique to or exacerbated by
the development and use of GAI are defined below. [5] Each risk is labeled according to the outcome,
object, or source of the risk (i.e., some are risks “to” a subject or domain and others are risks “of” or
“from” an issue or theme). These risks provide a lens through which organizations can frame and execute
risk management efforts. To help streamline risk management efforts, each risk is mapped in Section 3
(as well as in tables in Appendix B) to relevant Trustworthy AI Characteristics identified in the AI RMF.


5 These risks can be further categorized by organizations depending on their unique approaches to risk definition
and management. One possible way to further categorize these risks, derived in part from the [UK’s Internatonal](https://assets.publishing.service.gov.uk/media/6655982fdc15efdddf1a842f/international_scientific_report_on_the_safety_of_advanced_ai_interim_report.pdf)
[Scientfc Report on the Safety of Advanced AI, could be:](https://assets.publishing.service.gov.uk/media/6655982fdc15efdddf1a842f/international_scientific_report_on_the_safety_of_advanced_ai_interim_report.pdf) **1) Technical / Model risks (or risk from malfunction):**
Confabulation; Dangerous or Violent Recommendations; Data Privacy; Value Chain and Component Integration;
Harmful Bias, and Homogenization; **2) Misuse by humans (or malicious use):** CBRN Information or Capabilities;
Data Privacy; Human-AI Configuration; Obscene, Degrading, and/or Abusive Content; Information Integrity;
Information Security; **3) Ecosystem / societal risks (or systemic risks)** : Data Privacy; Environmental; Intellectual
Property. We also note that some risks are cross-cutting between these categories.


3


1. **CBRN Information or Capabilities:** Eased access to or synthesis of materially nefarious
information or design capabilities related to chemical, biological, radiological, or nuclear (CBRN)
weapons or other dangerous materials or agents.

2. **Confabulation:** The production of confidently stated but erroneous or false content (known
colloquially as “hallucinations” or “fabrications”) by which users may be misled or deceived. [6]

3. **Dangerous, Violent, or Hateful Content:** Eased production of and access to violent, inciting,
radicalizing, or threatening content as well as recommendations to carry out self-harm or
conduct illegal activities. Includes difficulty controlling public exposure to hateful and disparaging
or stereotyping content.

4. **Data Privacy:** Impacts due to leakage and unauthorized use, disclosure, or de-anonymization of
biometric, health, location, or other personally identifiable information or sensitive data. [7]

5. **Environmental Impacts:** Impacts due to high compute resource utilization in training or
operating GAI models, and related outcomes that may adversely impact ecosystems.

6. **Harmful Bias or Homogenization:** Amplification and exacerbation of historical, societal, and
systemic biases; performance disparities [8] between sub-groups or languages, possibly due to
non-representative training data, that result in discrimination, amplification of biases, or
incorrect presumptions about performance; undesired homogeneity that skews system or model
outputs, which may be erroneous, lead to ill-founded decision-making, or amplify harmful
biases.

7. **Human-AI Configuration:** Arrangements of or interactions between a human and an AI system
which can result in the human inappropriately anthropomorphizing GAI systems or experiencing
algorithmic aversion, automation bias, over-reliance, or emotional entanglement with GAI
systems.

8. **Information Integrity:** Lowered barrier to entry to generate and support the exchange and
consumption of content which may not distinguish fact from opinion or fiction or acknowledge
uncertainties, or could be leveraged for large-scale dis- and mis-information campaigns.

9. **Information Security:** Lowered barriers for offensive cyber capabilities, including via automated
discovery and exploitation of vulnerabilities to ease hacking, malware, phishing, offensive cyber


6 Some commenters have noted that the terms “hallucination” and “fabrication” anthropomorphize GAI, which
itself is a risk related to GAI systems as it can inappropriately attribute human characteristics to non-human
entities.
7 What is categorized as sensitive data or [sensitve PII can be highly contextual based on the nature of the](https://www.iso.org/obp/ui/#iso:std:iso-iec:29100:ed-2:v1:en)
information, but examples of sensitive information include information that relates to an information subject’s
most intimate sphere, including political opinions, sex life, or criminal convictions.
8 The notion of harm presumes some baseline scenario that the harmful factor (e.g., a GAI model) makes worse.
When the mechanism for potential harm is a disparity between groups, it can be difficult to establish what the
most appropriate baseline is to compare against, which can result in divergent views on when a disparity between
AI behaviors for different subgroups constitutes a harm. In discussing harms from disparities such as biased
behavior, this document highlights examples where someone’s situation is worsened relative to what it would have
been in the absence of any AI system, making the outcome unambiguously a harm of the system.


4


operations, or other cyberattacks; increased attack surface for targeted cyberattacks, which may
compromise a system’s availability or the confidentiality or integrity of training data, code, or
model weights.

10. **Intellectual Property:** Eased production or replication of alleged copyrighted, trademarked, or
licensed content without authorization (possibly in situations which do not fall under fair use);
eased exposure of trade secrets; or plagiarism or illegal replication.

11. **Obscene, Degrading, and/or Abusive Content:** Eased production of and access to obscene,
degrading, and/or abusive imagery which can cause harm, including synthetic child sexual abuse
material (CSAM), and nonconsensual intimate images (NCII) of adults.

12. **Value Chain and Component Integration:** Non-transparent or untraceable integration of
upstream third-party components, including data that has been improperly obtained or not
processed and cleaned due to increased automation from GAI; improper supplier vetting across
the AI lifecycle; or other issues that diminish transparency or accountability for downstream
users.


**2.1.** **CBRN Information or Capabilities**


In the future, GAI may enable malicious actors to more easily access CBRN weapons and/or relevant
knowledge, information, materials, tools, or technologies that could be misused to assist in the design,
development, production, or use of CBRN weapons or other dangerous materials or agents. While
relevant biological and chemical threat knowledge and information is often publicly accessible, LLMs
could facilitate its [analysis or synthesis, particularly by individuals without formal scientific training or](https://arxiv.org/abs/2306.03809)
expertise.

Recent research on this topic found that LLM outputs regarding [biological threat creaton and](https://openai.com/index/building-an-early-warning-system-for-llm-aided-biological-threat-creation/) [atack](https://www.rand.org/pubs/research_reports/RRA2977-2.html)
[planning](https://www.rand.org/pubs/research_reports/RRA2977-2.html) provided minimal assistance beyond traditional search engine queries, suggesting that state-ofthe-art LLMs at the time these studies were conducted do not substantially increase the operational
likelihood of such an attack. The physical synthesis development, production, and use of chemical or
biological agents will continue to require both applicable expertise and supporting materials and
infrastructure. The impact of GAI on chemical or biological agent misuse will depend on what the key
barriers for malicious actors are (e.g., whether information access is one such barrier), and how well GAI
can help actors address those barriers.

Furthermore, chemical and biological design tools (BDTs) – highly [specialized AI systems](https://arxiv.org/pdf/2306.13952) trained on
scientific data that aid in chemical and biological design – may augment design capabilities in chemistry
and biology beyond what text-based LLMs are able to provide. As these models become more
efficacious, including for beneficial uses, it will be important to assess their potential to be used for
harm, such as the ideation and design of novel harmful chemical or biological agents.

While some of these described capabilities lie beyond the reach of existing GAI tools, ongoing
assessments of this risk would be enhanced by monitoring both the ability of AI tools to facilitate CBRN
weapons planning and GAI systems’ connection or access to relevant data and tools.

**Trustworthy AI Characteristic:** Safe, Explainable and Interpretable


5


**2.2.** **Confabulation**


“Confabulation” refers to a phenomenon in which GAI systems generate and confidently present
erroneous or false content in response to prompts. Confabulations also include generated outputs that
diverge from the prompts or other input or that contradict previously generated statements in the same
context. These phenomena are colloquially also referred to as “hallucinations” or “fabrications.”

Confabulations can occur across GAI outputs and contexts. [9,10] Confabulations are a natural result of the
way generative models are [designed: they generate outputs that approximate the statistical distribution](https://arxiv.org/pdf/2311.14648)
of their training data; for example, LLMs [predict the next token or word](https://cset.georgetown.edu/article/the-surprising-power-of-next-word-prediction-large-language-models-explained-part-1/) in a sentence or phrase. While
such statistical prediction can produce factually accurate and consistent outputs, it can also produce
outputs that are factually inaccurate or internally inconsistent. This dynamic is particularly relevant when
it comes to open-ended prompts for [long-form responses and in](https://arxiv.org/pdf/2403.18802) [domains](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4696936) which require highly
contextual and/or domain expertise.

Risks from confabulations may arise when users believe false content – often due to the confident nature
of the response – leading users to act upon or promote the false information. This poses a challenge for
many real-world applications, such as in healthcare, where a confabulated summary of patient
information reports could cause doctors to make [incorrect diagnoses and/or recommend the wrong](https://dl.acm.org/doi/full/10.1145/3571730)
treatments. Risks of confabulated content may be especially important to monitor when integrating GAI
into applications involving consequential decision making.

GAI outputs may also include confabulated logic or citations that purport to justify or explain the
system’s answer, which may further mislead humans into inappropriately trusting the system’s output.
For instance, LLMs sometimes provide logical steps for how they arrived at an answer even when the
answer itself is incorrect. Similarly, an LLM could falsely assert that it is human or has human traits,
potentially deceiving humans into believing they are speaking with another human.

The extent to which humans can be deceived by LLMs, the mechanisms by which this may occur, and the
potential risks from adversarial prompting of such behavior are emerging areas of study. Given the wide
range of downstream impacts of GAI, it is difficult to estimate the downstream scale and impact of
confabulations.

**Trustworthy AI Characteristics:** Fair with Harmful Bias Managed, Safe, Valid and Reliable, Explainable
and Interpretable


**2.3.** **Dangerous, Violent, or Hateful Content**


GAI systems can produce content that is inciting, radicalizing, or threatening, or that glorifies violence,
with greater ease and scale than other technologies. LLMs have been [reported to generate](https://arxiv.org/pdf/2112.04359.pdf) dangerous or
violent recommendations, and some models have generated actionable instructions for dangerous or


9 Confabulations of falsehoods are most commonly a problem for text-based outputs; for audio, image, or video
content, creative generation of non-factual content can be a desired behavior.
10 For example, legal confabulations have been [shown to be pervasive](https://arxiv.org/abs/2401.01301) in current state-of-the-art LLMs. See also,
e.g.,


6


unethical behavior. Text-to-image models also make it easy to [create images](https://arxiv.org/pdf/2305.13873.pdf) that could be used to
promote dangerous or violent messages. Similar concerns are present for other GAI media, including
video and audio. GAI may also produce content that recommends self-harm or criminal/illegal activities.

Many current systems [restrict model outputs](https://arxiv.org/pdf/2303.08774.pdf) to limit certain content or in response to certain prompts,
but this approach may [stll produce harmful recommendatons](https://arxiv.org/pdf/2308.13387.pdf) in response to other less-explicit, novel
prompts (also relevant to CBRN Information or Capabilities, Data Privacy, Information Security, and
Obscene, Degrading and/or Abusive Content). Crafting such prompts deliberately is known as
[“jailbreaking,” or, manipulating prompts to circumvent output controls. Limitations of GAI systems can be](https://arxiv.org/html/2403.17336v1)
harmful or dangerous in certain contexts. Studies have observed that users may [disclose mental health](https://www.hbs.edu/ris/Publication%20Files/23-011_c1bdd417-f717-47b6-bccb-5438c6e65c1a_f6fd9798-3c2d-4932-b222-056231fe69d7.pdf)
[issues in conversations with chatbots – and that users exhibit negative reactions to unhelpful responses](https://www.hbs.edu/ris/Publication%20Files/23-011_c1bdd417-f717-47b6-bccb-5438c6e65c1a_f6fd9798-3c2d-4932-b222-056231fe69d7.pdf)
from these chatbots during situations of distress.

This risk encompasses difficulty controlling creation of and public exposure to offensive or hateful
language, and denigrating or stereotypical content generated by AI. This kind of speech may contribute
to downstream harm such as fueling dangerous or violent behaviors. The spread of denigrating or
stereotypical content can also further exacerbate [representatonal harms](https://dl.acm.org/doi/10.1609/aaai.v37i12.26670) (see Harmful Bias and
Homogenization below).

**Trustworthy AI Characteristics:** Safe, Secure and Resilient


**2.4.** **Data Privacy**


GAI systems [raise several risks to privacy. GAI system training requires large volumes of data, which in](https://arxiv.org/pdf/2310.07879)
some cases may include personal data. The use of personal data for GAI training raises risks to [widely](https://www.whitehouse.gov/wp-content/uploads/legacy_drupal_files/omb/circulars/A130/a130revised.pdf)
[accepted privacy principles, including to transparency, individual participation (including consent), and](https://www.whitehouse.gov/wp-content/uploads/legacy_drupal_files/omb/circulars/A130/a130revised.pdf)
purpose specification. For example, most model developers do not disclose specific data sources on
which models were trained, limiting user awareness of whether personally identifiably information (PII)
was trained on and, if so, how it was collected.

Models may leak, generate, or correctly infer sensitive information about individuals. For example,
during adversarial attacks, LLMs have revealed [sensitve informaton](https://www.usenix.org/conference/usenixsecurity21/presentation/carlini-extracting) (from the public domain) that was
included in their training data. This problem has been referred to as [data memorizaton, and may pose](https://arxiv.org/pdf/2202.07646)
exacerbated privacy risks even for data present only in a [small number of training samples.](https://www.usenix.org/system/files/sec21-carlini-extracting.pdf)

In addition to revealing sensitive information in GAI training data, GAI models may be able to [correctly](https://arxiv.org/pdf/2310.07298)
[infer PII or sensitive data that was not in their training data nor disclosed by the user by stitching](https://arxiv.org/pdf/2310.07298)
together information from disparate sources. These inferences can have negative impact on an individual
even if the inferences are not accurate (e.g., confabulations), and especially if they reveal information
that the individual considers sensitive or that is used to [disadvantage or harm them.](https://dl.acm.org/doi/pdf/10.1145/3531146.3533088)

Beyond harms from information exposure (such as extortion or dignitary harm), wrong or inappropriate
inferences of PII can contribute to downstream or secondary harmful impacts. For example, predictive
inferences made by GAI models based on PII or protected attributes can contribute to [adverse decisions,](https://arxiv.org/pdf/2210.05791)
leading to representational or allocative harms to individuals or groups (see Harmful Bias and
Homogenization below).


7


**Trustworthy AI Characteristics:** Accountable and Transparent, Privacy Enhanced, Safe, Secure and
Resilient


**2.5.** **Environmental Impacts**


Training, maintaining, and operating (running inference on) GAI systems are resource-intensive activities,
with potentially large energy and environmental footprints. Energy and carbon emissions [vary](https://aclanthology.org/2023.findings-emnlp.607.pdf) based on
what is being done with the GAI model (i.e., pre-training, fine-tuning, inference), the modality of the
content, hardware used, and type of task or application.

[Current estimates suggest that training a single transformer LLM can emit as much carbon](https://arxiv.org/pdf/1906.02243.pdf) as 300 roundtrip flights between San Francisco and New York. In a study comparing energy consumption and carbon
[emissions for LLM inference, generative tasks (e.g., text summarization) were found to be more energy-](https://arxiv.org/pdf/2311.16863)
[and carbon-intensive than discriminative or non-generative tasks (e.g., text classification).](https://arxiv.org/pdf/2311.16863)

Methods for creating smaller versions of trained models, such as model distillation or compression,
[could reduce](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0285668) environmental impacts at inference time, but training and tuning such models may still
contribute to their environmental impacts. Currently there is no agreed upon method to estimate
environmental impacts from GAI.

**Trustworthy AI Characteristics:** Accountable and Transparent, Safe


**2.6.** **Harmful Bias and Homogenization**


Bias exists [in many forms](https://www.nist.gov/publications/towards-standard-identifying-and-managing-bias-artificial-intelligence) and can become ingrained in automated systems. AI systems, including GAI
systems, can increase the speed and scale at which harmful biases manifest and are acted upon,
potentially perpetuating and amplifying harms to individuals, groups, communities, organizations, and
society. For example, when prompted to generate images of CEOs, doctors, lawyers, and judges, current
text-to-image models [underrepresent women and/or racial minorities, and people with disabilities.](https://www.bloomberg.com/graphics/2023-generative-ai-bias/)
Image generator models have also produced biased or stereotyped output for various demographic
groups and have difficulty producing non-stereotyped content even when the prompt specifically
requests image features that are inconsistent with the stereotypes. Harmful bias in GAI models, which
may stem from their training data, can also cause representational harms or [perpetuate or exacerbate](https://www.bloomberg.com/graphics/2024-openai-gpt-hiring-racial-discrimination/?accessToken=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzb3VyY2UiOiJTdWJzY3JpYmVyR2lmdGVkQXJ0aWNsZSIsImlhdCI6MTcwOTg1NjE0OCwiZXhwIjoxNzEwNDYwOTQ4LCJhcnRpY2xlSWQiOiJTQTA1Q1FUMEFGQjQwMCIsImJjb25uZWN0SWQiOiI2NDU1MEM3NkRFMkU0QkM1OEI0OTI5QjBDQkIzRDlCRCJ9.MdkSGC3HMwwUYtltWq6WxWg3vULNeCTJcjacB-DNi8k)
bias based on race, gender, disability, or other protected classes.

Harmful bias in GAI systems can also lead to harms via disparities between how a model performs for
different subgroups or languages (e.g., an LLM may perform less well for [non-English languages](https://aclanthology.org/2023.emnlp-main.491.pdf) or
certain dialects). Such disparities can contribute to discriminatory decision-making or amplification of
existing societal biases. In addition, GAI systems may be inappropriately trusted to perform similarly
across all subgroups, which could leave the groups facing underperformance with worse outcomes than
if no GAI system were used. Disparate or reduced performance for lower-resource languages also
presents challenges to model adoption, inclusion, and accessibility, and may make preservation of
[endangered languages](https://policyreview.info/pdf/policyreview-2022-2-1654.pdf) more difficult if GAI systems become embedded in everyday processes that would
otherwise have been opportunities to use these languages.

Bias is mutually reinforcing with the problem of undesired homogenization, in which GAI systems
produce skewed distributions of outputs that are overly uniform (for example, [repettve aesthetc styles](https://www.science.org/doi/10.1126/science.adh4451)


8


and [reduced content diversity). Overly homogenized outputs can themselves be incorrect, or they may](https://arxiv.org/pdf/2309.05196.pdf)
lead to unreliable decision-making or amplify harmful biases. These phenomena [can fow from](https://arxiv.org/pdf/2211.13972.pdf)
foundation models to downstream models and systems, with the foundation models acting as
[“botlenecks,” or single points of failure.](https://arxiv.org/pdf/2305.08157.pdf)

[Overly homogenized content can contribute to “model collapse.” Model collapse can occur when model](https://arxiv.org/pdf/2305.17493v2.pdf)
training over-relies on synthetic data, resulting in data points disappearing from the distribution of the
new model’s outputs. In addition to threatening the robustness of the model overall, model collapse
could lead to homogenized outputs, including by amplifying any homogenization from the model used to
generate the synthetic training data.

**Trustworthy AI Characteristics:** Fair with Harmful Bias Managed, Valid and Reliable


**2.7.** **Human-AI Configuration**


GAI system use can involve varying risks of misconfigurations and poor interactions between a system
and a human who is interacting with it. Humans bring their unique perspectives, experiences, or domainspecific expertise to interactions with AI systems but may not have detailed knowledge of AI systems and
[how they work. As a result, human experts may be unnecessarily “averse” to GAI systems, and thus](https://marketing.wharton.upenn.edu/wp-content/uploads/2016/10/Dietvorst-Simmons-Massey-2014.pdf)
deprive themselves or others of GAI’s beneficial uses.

Conversely, due to the complexity and increasing reliability of GAI technology, over time, humans may
[over-rely on GAI systems or may unjustifiably perceive](https://doi.org/10.1017/jdm.2023.37) GAI content to be of higher quality than that
produced by other sources. This phenomenon is an example of [automaton bias, or excessive deference](https://academic.oup.com/jcmc/article/28/1/zmac029/6827859)
to automated systems. Automation bias can exacerbate other risks of GAI, such as risks of confabulation
or risks of bias or homogenization.

There may also be concerns about [emotonal entanglement](https://www.researchgate.net/publication/374505266_Ethical_Tensions_in_Human-AI_Companionship_A_Dialectical_Inquiry_into_Replika) between humans and GAI systems, which
could lead to negative psychological impacts.

**Trustworthy AI Characteristics:** Accountable and Transparent, Explainable and Interpretable, Fair with
Harmful Bias Managed, Privacy Enhanced, Safe, Valid and Reliable


**2.8.** **Information Integrity**


[Informaton integrity](https://www.whitehouse.gov/wp-content/uploads/2022/12/Roadmap-Information-Integrity-RD-2022.pdf?_hsenc=p2ANqtz-_x-sgb3MM0fsqqLg3Vz4Vten0hlnHejas4CchT-Z59EnsVTC5XWcZHb2T4TR9Tz2TDQTP8lpdwR8PiDSI4GNApCIykTA) describes the “spectrum of information and associated patterns of its creation,
exchange, and consumption in society.” High-integrity information can be trusted; “distinguishes fact
from fiction, opinion, and inference; acknowledges uncertainties; and is transparent about its level of
vetting. This information can be linked to the original source(s) with appropriate evidence. High-integrity
information is also accurate and reliable, can be verified and authenticated, has a clear chain of custody,
and creates reasonable expectations about when its validity may expire.” [11]


11 This definition of information integrity is derived from the 2022 White House Roadmap for Researchers on
Priorities Related to Information Integrity Research and Development.


9


GAI systems can ease the unintentional production or dissemination of false, inaccurate, or misleading
content (misinformation) at scale, particularly if the content stems from confabulations.

GAI systems can also ease the deliberate production or dissemination of [false or misleading informaton](https://rm.coe.int/information-disorder-toward-an-interdisciplinary-framework-for-researc/168076277c)
(disinformation) at scale, where an actor has the explicit intent to deceive or cause harm to others. Even
very [subtle changes](https://deepmind.google/discover/blog/images-altered-to-trick-machine-vision-can-influence-humans-too/) to text or images can manipulate human and machine perception.

Similarly, GAI systems could enable a [higher degree of sophistcaton](https://www.rand.org/pubs/commentary/2023/10/dismantling-the-disinformation-business-of-chinese.html) for malicious actors to produce
disinformation that is targeted towards specific demographics. Current and emerging multimodal models
[make it possible to generate both text-based disinformation and highly realistic “deepfakes” – that is,](https://www.nytimes.com/2023/02/07/technology/artificial-intelligence-training-deepfake.html)
synthetic audiovisual content and photorealistic images. [12] Additional disinformation threats could be
enabled by future GAI models trained on new data modalities.

[Disinformation and misinformation – both of which may be facilitated by GAI – may erode public trust](https://arxiv.org/pdf/2310.11986.pdf) in
true or valid evidence and information, with downstream effects. For example, a synthetic image of a
Pentagon blast [went viral](https://www.bloomberg.com/news/articles/2023-05-22/fake-ai-photo-of-pentagon-blast-goes-viral-trips-stocks-briefly) and briefly caused a drop in the stock market. Generative AI models can also
assist malicious actors in creating compelling imagery and propaganda to support disinformation
campaigns, which may not be photorealistic, but could enable these campaigns to gain more reach and
engagement on social media platforms. Additionally, generative AI models can assist malicious actors in
creating fraudulent content intended to impersonate others.

**Trustworthy AI Characteristics:** Accountable and Transparent, Safe, Valid and Reliable, Interpretable and
Explainable


**2.9.** **Information Security**


Information security for computer systems and data is a mature field with widely accepted and
standardized practices for offensive and defensive cyber capabilities. GAI-based systems present two
primary information security risks: GAI could potentially discover or enable new cybersecurity risks by
lowering the barriers for or easing automated exercise of offensive capabilities; simultaneously, it
expands the available attack surface, as GAI itself is vulnerable to attacks like [prompt injecton](https://www.wired.co.uk/article/generative-ai-prompt-injection-hacking) or data
poisoning.

Offensive cyber capabilities advanced by GAI systems may augment cybersecurity attacks such as
hacking, malware, and phishing. Reports have indicated that LLMs are already able to [discover some](https://arxiv.org/pdf/2305.15324.pdf)
[vulnerabilites](https://arxiv.org/pdf/2305.15324.pdf) in systems (hardware, software, data) and write code to [exploit them. Sophisticated threat](https://googleprojectzero.blogspot.com/2024/06/project-naptime.html)
actors might further these risks by developing [GAI-powered security co-pilots](https://www.paloaltonetworks.com/blog/2024/02/impacts-of-ai-in-cybersecurity/) for use in several parts of
the attack chain, including informing attackers on how to proactively evade threat detection and escalate
privileges after gaining system access.

Information security for GAI models and systems also includes maintaining availability of the GAI system
and the integrity and (when applicable) the confidentiality of the GAI code, training data, and model
weights. To identify and secure potential attack points in AI systems or specific components of the AI


12 See also https://doi.org/10.6028/NIST.AI.100-4, to be published.


10


value chain (e.g., data inputs, processing, GAI training, or deployment environments), conventional
cybersecurity practices may need to [adapt or evolve.](https://www.mandiant.com/resources/blog/securing-ai-pipeline)

For instance, prompt injection involves modifying what input is provided to a GAI system so that it
behaves in unintended ways. In direct prompt injections, attackers might craft malicious prompts and
input them directly to a GAI system, with a variety of downstream negative consequences to
interconnected systems. [Indirect prompt injecton](https://arxiv.org/abs/2302.12173) attacks occur when adversaries remotely (i.e., without
a direct interface) exploit LLM-integrated applications by injecting prompts into data likely to be
retrieved. Security researchers have already demonstrated how indirect prompt injections can exploit
vulnerabilities by [stealing proprietary data or running malicious code remotely](https://embracethered.com/blog/posts/2023/bing-chat-data-exfiltration-poc-and-fix/) on a machine. Merely
[querying](https://arxiv.org/abs/2403.06634) a closed production model can elicit previously undisclosed information about that model.

Another cybersecurity risk to GAI is [data poisoning, in which an adversary](https://www.crowdstrike.com/cybersecurity-101/cyberattacks/data-poisoning/) [compromises](https://csrc.nist.gov/pubs/ai/100/2/e2023/final) a training
dataset used by a model to manipulate its outputs or operation. Malicious tampering with data or parts
of the model could exacerbate risks associated with GAI system outputs.

**Trustworthy AI Characteristics:** Privacy Enhanced, Safe, Secure and Resilient, Valid and Reliable


**2.10.** **Intellectual Property**


Intellectual property risks from GAI systems may arise where the use of copyrighted works is not a fair
use under the fair use doctrine. If a GAI system’s training data included copyrighted material, GAI
outputs displaying instances of training [data memorizaton](https://www.usenix.org/conference/usenixsecurity21/presentation/carlini-extracting) (see Data Privacy above) could infringe on
copyright.

How GAI relates to copyright, including the status of generated content that is similar to but [does not](https://dl.acm.org/doi/10.1145/3531146.3533088)
[strictly copy work protected by copyright, is currently being debated in legal fora. Similar discussions are](https://dl.acm.org/doi/10.1145/3531146.3533088)
taking place regarding the use or emulation of personal identity, likeness, or voice without permission.

**Trustworthy AI Characteristics:** Accountable and Transparent, Fair with Harmful Bias Managed, Privacy
Enhanced


**2.11.** **Obscene, Degrading, and/or Abusive Content**


GAI can ease the production of and access to illegal non-consensual intimate imagery (NCII) of adults,
and/or child sexual abuse material (CSAM). GAI-generated obscene, abusive or degrading content can
create privacy, psychological and emotional, and even physical harms, and in some cases may be illegal.

Generated explicit or obscene AI content may include highly realistic “deepfakes” of [real individuals,](https://incidentdatabase.ai/blog/deepfakes-and-child-safety/)
including children. The spread of this kind of material can have downstream negative consequences: in
the context of CSAM, even if the generated images do not resemble specific individuals, the prevalence
of such images can divert time and resources from efforts to find real-world victims. Outside of CSAM,
the creation and spread of NCII disproportionately impacts [women and](https://www.brookings.edu/articles/ai-poses-disproportionate-risks-to-women/) [sexual minorites, and can have](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC9554400/)
[subsequent](https://journals.sagepub.com/doi/full/10.1177/08862605221122834#bibr47-08862605221122834) negative consequences including decline in overall mental health, substance abuse, and
even suicidal thoughts.

Data used for training GAI models may unintentionally include CSAM and NCII. A [recent report](https://cyber.fsi.stanford.edu/news/investigation-finds-ai-image-generation-models-trained-child-abuse) noted
that several commonly used GAI training datasets were found to contain hundreds of known images of


11


CSAM. Even when trained on “clean” data, increasingly capable GAI models can synthesize or produce
synthetic NCII and CSAM. Websites, mobile apps, and custom-built models that generate synthetic NCII
have [moved from niche internet forums to mainstream, automated, and scaled online businesses.](https://graphika.com/reports/a-revealing-picture)

**Trustworthy AI Characteristics:** Fair with Harmful Bias Managed, Safe, Privacy Enhanced


**2.12.** **Value Chain and Component Integration**


GAI value chains involve many [third-party components](https://partnershiponai.org/from-code-to-consumer-pais-value-chain-analysis-illuminates-generative-ais-key-players/) such as procured datasets, pre-trained models,
and software libraries. These components might be improperly obtained or not properly vetted, leading
to diminished transparency or accountability for downstream users. While this is a risk for traditional AI
systems and some other digital technologies, the risk is exacerbated for GAI due to the scale of the
training data, which may be too large for humans to vet; the difficulty of training foundation models,
which leads to extensive reuse of limited numbers of models; and the extent to which GAI may be
integrated into other devices and services. As GAI systems often involve many distinct third-party
components and data sources, it may be difficult to attribute issues in a system’s behavior to any one of
these sources.

Errors in third-party GAI components can also have downstream impacts on accuracy and robustness.
For example, test datasets commonly used to benchmark or validate models can contain [label errors.](https://arxiv.org/pdf/2103.14749.pdf)
Inaccuracies in these labels can impact the “stability” or robustness of these benchmarks, which many
GAI practitioners consider during the model selection process.

**Trustworthy AI Characteristics:** Accountable and Transparent, Explainable and Interpretable, Fair with
Harmful Bias Managed, Privacy Enhanced, Safe, Secure and Resilient, Valid and Reliable


**3.** **Suggested Actions to Manage GAI Risks**


The following suggested actions target risks unique to or exacerbated by GAI.

In addition to the suggested actions below, AI risk management activities and actions set forth in the AI
RMF 1.0 and Playbook are already applicable for managing GAI risks. Organizations are encouraged to
apply the activities suggested in the AI RMF and its Playbook when managing the risk of GAI systems.

Implementation of the suggested actions will vary depending on the type of risk, characteristics of GAI
systems, stage of the GAI lifecycle, and relevant AI actors involved.

Suggested actions to manage GAI risks can be found in the tables below:

  - The suggested actions are **organized by relevant AI RMF subcategories** to streamline these
activities alongside implementation of the AI RMF.

  - **Not every subcategory of the AI RMF is included in this document.** [13] Suggested actions are
listed for only some subcategories.


13 As this document was focused on the GAI PWG efforts and primary considerations (see Appendix A), AI RMF
subcategories not addressed here may be added later.


12


     - Not every suggested action applies to **every** AI Actor [14] or is relevant to every AI Actor Task. For
example, suggested actions relevant to GAI developers may not be relevant to GAI deployers.
The applicability of suggested actions to relevant AI actors should be determined based on
organizational considerations and their unique uses of GAI systems.

Each table of suggested actions includes:

     - **Action ID:** Each Action ID corresponds to the relevant AI RMF function and subcategory (e.g., GV1.1-001 corresponds to the first suggested action for Govern 1.1, GV-1.1-002 corresponds to the
second suggested action for Govern 1.1). AI RMF functions are tagged as follows: GV = Govern;
MP = Map; MS = Measure; MG = Manage.

     - **Suggested Action:** Steps an organization or AI actor can take to manage GAI risks.

     - **GAI Risks:** Tags linking suggested actions with relevant GAI risks.

     - **AI Actor Tasks:** Pertinent [AI Actor Tasks](https://airc.nist.gov/AI_RMF_Knowledge_Base/AI_RMF/Appendices/Appendix_A#:%7E:text=AI%20actors%20in%20this%20category,data%20providers%2C%20system%20funders%2C%20product) for each subcategory. Not every AI Actor Task listed will
apply to every suggested action in the subcategory (i.e., some apply to AI development and
others apply to AI deployment).

The tables below begin with the AI RMF subcategory, shaded in blue, followed by suggested actions.


|GOVERN 1.1: Legal and regulatory requirements involving AI are understood, managed, and documented.|Col2|Col3|
|---|---|---|
|**Acton ID**|**Suggested Acton**|**GAI Risks**|
|GV-1.1-001|Align GAI development and use with applicable laws and regulatons, including<br>those related to data privacy, copyright and intellectual property law.|Data Privacy; Harmful Bias and<br>Homogenizaton; Intellectual<br>Property|
|**AI Actor Tasks: Governance and Oversight**|**AI Actor Tasks: Governance and Oversight**|**AI Actor Tasks: Governance and Oversight**|


14 AI Actors are defined by the OECD as “those who play an active role in the AI system lifecycle, including
organizations and individuals that deploy or operate AI.” See Appendix A of the AI RMF for additional descriptions
of AI Actors and AI Actor Tasks.


13


|GOVERN 1.2: The characteristics of trustworthy AI are integrated into organizational policies, processes, procedures, and practices.|Col2|Col3|
|---|---|---|
|**Acton ID**|**Suggested Acton**|**GAI Risks**|
|GV-1.2-001|Establish transparency policies and processes for documentng the origin and<br>history of training data and generated data for GAI applicatons to advance digital<br>content transparency, while balancing the proprietary nature of training<br>approaches.|Data Privacy; Informaton<br>Integrity; Intellectual Property|
|GV-1.2-002|Establish policies to evaluate risk-relevant capabilites of GAI and robustness of<br>safety measures, both prior to deployment and on an ongoing basis, through<br>internal and external evaluatons.|CBRN Informaton or Capabilites;<br>Informaton Security|
|**AI Actor Tasks: Governance and Oversight**|**AI Actor Tasks: Governance and Oversight**|**AI Actor Tasks: Governance and Oversight**|


|GOVERN 1.3: Processes, procedures, and practices are in place to determine the needed level of risk management activities based<br>on the organization’s risk tolerance.|Col2|Col3|
|---|---|---|
|**Acton ID**|**Suggested Acton**|**GAI Risks**|
|GV-1.3-001|Consider the following factors when updatng or deﬁning risk ters for GAI: Abuses<br>and impacts to informaton integrity; Dependencies between GAI and other IT or<br>data systems; Harm to fundamental rights or public safety; Presentaton of<br>obscene, objectonable, oﬀensive, discriminatory, invalid or untruthful output;<br>Psychological impacts to humans (e.g., anthropomorphizaton, algorithmic<br>aversion, emotonal entanglement); Possibility for malicious use; Whether the<br>system introduces signiﬁcant new security vulnerabilites; Antcipated system<br>impact on some groups compared to others; Unreliable decision making<br>capabilites, validity, adaptability, and variability of GAI system performance over<br>tme.|Informaton Integrity; Obscene,<br>Degrading, and/or Abusive<br>Content; Value Chain and<br>Component Integraton; Harmful<br>Bias and Homogenizaton;<br>Dangerous, Violent, or Hateful<br>Content; CBRN Informaton or<br>Capabilites|
|GV-1.3-002|Establish minimum thresholds for performance or assurance criteria and review as<br>part of deployment approval (“go/”no-go”) policies, procedures, and processes,<br>with reviewed processes and approval thresholds reﬂectng measurement of GAI<br>capabilites and risks.|CBRN Informaton or Capabilites;<br>Confabulaton; Dangerous,<br>Violent, or Hateful Content|
|GV-1.3-003|Establish a test plan and response policy, before developing highly capable models,<br>to periodically evaluate whether the model may misuse CBRN informaton or<br>capabilites and/or oﬀensive cyber capabilites.|CBRN Informaton or Capabilites;<br>Informaton Security|


14


|GV-1.3-004|Obtain input from stakeholder communities to identify unacceptable use, in<br>accordance with activities in the AI RMF Map function.|CBRN Information or Capabilities;<br>Obscene, Degrading, and/or<br>Abusive Content; Harmful Bias<br>and Homogenization; Dangerous,<br>Violent, or Hateful Content|
|---|---|---|
|GV-1.3-005|Maintain an updated hierarchy of identﬁed and expected GAI risks connected to<br>contexts of GAI model advancement and use, potentally including specialized risk<br>levels for GAI systems that address issues such as model collapse and algorithmic<br>monoculture.|Harmful Bias and Homogenizaton|
|GV-1.3-006|Reevaluate organizatonal risk tolerances to account for unacceptable negatve risk<br>(such as where signiﬁcant negatve impacts are imminent, severe harms are<br>actually occurring, or large-scale risks could occur); and broad GAI negatve risks,<br>including: Immature safety or risk cultures related to AI and GAI design,<br>development and deployment, public informaton integrity risks, including impacts<br>on democratc processes, unknown long-term performance characteristcs of GAI.|Informaton Integrity; Dangerous,<br>Violent, or Hateful Content; CBRN<br>Informaton or Capabilites|
|GV-1.3-007|Devise a plan to halt development or deployment of a GAI system that poses<br>unacceptable negatve risk.|CBRN Informaton and Capability;<br>Informaton Security; Informaton<br>Integrity|
|**AI Actor Tasks: Governance and Oversight**|**AI Actor Tasks: Governance and Oversight**|**AI Actor Tasks: Governance and Oversight**|


|GOVERN 1.4: The risk management process and its outcomes are established through transparent policies, procedures, and other<br>controls based on organizational risk priorities.|Col2|Col3|
|---|---|---|
|**Acton ID**|**Suggested Acton**|**GAI Risks**|
|GV-1.4-001|Establish policies and mechanisms to prevent GAI systems from generatng<br>CSAM, NCII or content that violates the law.|Obscene, Degrading, and/or<br>Abusive Content; Harmful Bias<br>and Homogenizaton;<br>Dangerous, Violent, or Hateful<br>Content|
|GV-1.4-002|Establish transparent acceptable use policies for GAI that address illegal use or<br>applicatons of GAI.|CBRN Informaton or<br>Capabilites; Obscene,<br>Degrading, and/or Abusive<br>Content; Data Privacy; Civil<br>Rights violatons|
|**AI Actor Tasks: AI Development, AI Deployment, Governance and Oversight**|**AI Actor Tasks: AI Development, AI Deployment, Governance and Oversight**|**AI Actor Tasks: AI Development, AI Deployment, Governance and Oversight**|


15


|GOVERN 1.5: Ongoing monitoring and periodic review of the risk management process and its outcomes are planned, and<br>organizational roles and responsibilities are clearly defined, including determining the frequency of periodic review.|Col2|Col3|
|---|---|---|
|**Acton ID**|**Suggested Acton**|**GAI Risks**|
|GV-1.5-001|Deﬁne organizatonal responsibilites for periodic review of content provenance<br>and incident monitoring for GAI systems.|Informaton Integrity|
|GV-1.5-002|Establish organizatonal policies and procedures for afer acton reviews of GAI<br>system incident response and incident disclosures, to identfy gaps; Update<br>incident response and incident disclosure processes as required.|Human-AI Conﬁguraton;<br>Informaton Security|
|GV-1.5-003|Maintain a document retenton policy to keep history for test, evaluaton,<br>validaton, and veriﬁcaton (TEVV), and digital content transparency methods for<br>GAI.|Informaton Integrity; Intellectual<br>Property|
|**AI Actor Tasks: Governance and Oversight, Operaton and Monitoring**|**AI Actor Tasks: Governance and Oversight, Operaton and Monitoring**|**AI Actor Tasks: Governance and Oversight, Operaton and Monitoring**|


|GOVERN 1.6: Mechanisms are in place to inventory AI systems and are resourced according to organizational risk priorities.|Col2|Col3|
|---|---|---|
|**Acton ID**|**Suggested Acton**|**GAI Risks**|
|GV-1.6-001|Enumerate organizatonal GAI systems for incorporaton into AI system inventory<br>and adjust AI system inventory requirements to account for GAI risks.|Informaton Security|
|GV-1.6-002|Deﬁne any inventory exemptons in organizatonal policies for GAI systems<br>embedded into applicaton sofware.|Value Chain and Component<br>Integraton|
|GV-1.6-003|In additon to general model, governance, and risk informaton, consider the<br>following items in GAI system inventory entries: Data provenance informaton<br>(e.g., source, signatures, versioning, watermarks); Known issues reported from<br>internal bug tracking or external informaton sharing resources (e.g., AI incident <br>database, AVID, CVE, NVD, or OECD AI incident monitor); Human oversight roles<br>and responsibilites; Special rights and consideratons for intellectual property,<br>licensed works, or personal, privileged, proprietary or sensitve data; Underlying<br>foundaton models, versions of underlying models, and access modes.|Data Privacy; Human-AI<br>Conﬁguraton; Informaton<br>Integrity; Intellectual Property;<br>Value Chain and Component<br>Integraton|
|**AI Actor Tasks: Governance and Oversight**|**AI Actor Tasks: Governance and Oversight**|**AI Actor Tasks: Governance and Oversight**|


16


|GOVERN 1.7: Processes and procedures are in place for decommissioning and phasing out AI systems safely and in a manner that<br>does not increase risks or decrease the organization’s trustworthiness.|Col2|Col3|
|---|---|---|
|**Acton ID**|**Suggested Acton**|**GAI Risks**|
|GV-1.7-001|Protocols are put in place to ensure GAI systems are able to be deactvated when<br>necessary.|Informaton Security; Value Chain<br>and Component Integraton|
|GV-1.7-002|Consider the following factors when decommissioning GAI systems: Data<br>retenton requirements; Data security, e.g., containment, protocols, Data leakage<br>afer decommissioning; Dependencies between upstream, downstream, or other<br>data, internet of things (IOT) or AI systems; Use of open-source data or models;<br>Users’ emotonal entanglement with GAI functons.|Human-AI Conﬁguraton;<br>Informaton Security; Value Chain<br>and Component Integraton|
|**AI Actor Tasks: AI Deployment, Operaton and Monitoring** <br>|**AI Actor Tasks: AI Deployment, Operaton and Monitoring** <br>|**AI Actor Tasks: AI Deployment, Operaton and Monitoring** <br>|


|GOVERN 2.1: Roles and responsibilities and lines of communication related to mapping, measuring, and managing AI risks are<br>documented and are clear to individuals and teams throughout the organization.|Col2|Col3|
|---|---|---|
|**Acton ID**|**Suggested Acton**|**GAI Risks**|
|GV-2.1-001|Establish organizatonal roles, policies, and procedures for communicatng GAI<br>incidents and performance to AI Actors and downstream stakeholders (including<br>those potentally impacted), via community or oﬃcial resources (e.g., AI incident <br>database, AVID, CVE, NVD, or OECD AI incident monitor).|Human-AI Conﬁguraton; Value<br>Chain and Component Integraton|
|GV-2.1-002|Establish procedures to engage teams for GAI system incident response with<br>diverse compositon and responsibilites based on the partcular incident type.|Harmful Bias and Homogenizaton|
|GV-2.1-003|Establish processes to verify the AI Actors conductng GAI incident response tasks<br>demonstrate and maintain the appropriate skills and training.|Human-AI Conﬁguraton|
|GV-2.1-004|When systems may raise natonal security risks, involve natonal security<br>professionals in mapping, measuring, and managing those risks.|CBRN Informaton or Capabilites;<br>Dangerous, Violent, or Hateful<br>Content; Informaton Security|
|GV-2.1-005|Create mechanisms to provide protectons for whistleblowers who report, based<br>on reasonable belief, when the organizaton violates relevant laws or poses a<br>speciﬁc and empirically well-substantated negatve risk to public safety (or has<br>already caused harm).|CBRN Informaton or Capabilites;<br>Dangerous, Violent, or Hateful<br>Content|
|**AI Actor Tasks: Governance and Oversight**|**AI Actor Tasks: Governance and Oversight**|**AI Actor Tasks: Governance and Oversight**|


17


|GOVERN 3.2: Policies and procedures are in place to define and differentiate roles and responsibilities for human-AI configurations<br>and oversight of AI systems.|Col2|Col3|
|---|---|---|
|**Acton ID**|**Suggested Acton**|**GAI Risks**|
|GV-3.2-001|Policies are in place to bolster oversight of GAI systems with independent<br>evaluatons or assessments of GAI models or systems where the type and<br>robustness of evaluatons are proportonal to the identﬁed risks.|CBRN Informaton or Capabilites;<br>Harmful Bias and Homogenizaton|
|GV-3.2-002|Consider adjustment of organizatonal roles and components across lifecycle<br>stages of large or complex GAI systems, including: Test and evaluaton, validaton,<br>and red-teaming of GAI systems; GAI content moderaton; GAI system<br>development and engineering; Increased accessibility of GAI tools, interfaces, and<br>systems, Incident response and containment.|Human-AI Conﬁguraton;<br>Informaton Security; Harmful Bias<br>and Homogenizaton|
|GV-3.2-003|Deﬁne acceptable use policies for GAI interfaces, modalites, and human-AI<br>conﬁguratons (i.e., for chatbots and decision-making tasks), including criteria for<br>the kinds of queries GAI applicatons should refuse to respond to.|Human-AI Conﬁguraton|
|GV-3.2-004|Establish policies for user feedback mechanisms for GAI systems which include<br>thorough instructons and any mechanisms for recourse.|Human-AI Conﬁguraton|
|GV-3.2-005|Engage in threat modeling to antcipate potental risks from GAI systems.|CBRN Informaton or Capabilites;<br>Informaton Security|
|**AI Actors: AI Design**|**AI Actors: AI Design**|**AI Actors: AI Design**|


|GOVERN 4.1: Organizational policies and practices are in place to foster a critical thinking and safety-first mindset in the design,<br>development, deployment, and uses of AI systems to minimize potential negative impacts.|Col2|Col3|
|---|---|---|
|**Acton ID**|**Suggested Acton**|**GAI Risks**|
|GV-4.1-001|Establish policies and procedures that address contnual improvement processes<br>for GAI risk measurement. Address general risks associated with a lack of<br>explainability and transparency in GAI systems by using ample documentaton and<br>techniques such as: applicaton of gradient-based atributons, occlusion/term<br>reducton, counterfactual prompts and prompt engineering, and analysis of<br>embeddings; Assess and update risk measurement approaches at regular<br>cadences.|Confabulaton|
|GV-4.1-002|Establish policies, procedures, and processes detailing risk measurement in<br>context of use with standardized measurement protocols and structured public<br>feedback exercises such as AI red-teaming or independent external evaluatons.|CBRN Informaton and Capability;<br>Value Chain and Component<br>Integraton|


18


|GV-4.1-003|Establish policies, procedures, and processes for oversight functions (e.g., senior<br>leadership, legal, compliance, including internal evaluation) across the GAI<br>lifecycle, from problem formulation and supply chains to system decommission.|Value Chain and Component<br>Integration|
|---|---|---|
|**AI Actor Tasks: AI Deployment, AI Design, AI Development, Operaton and Monitoring**|**AI Actor Tasks: AI Deployment, AI Design, AI Development, Operaton and Monitoring**|**AI Actor Tasks: AI Deployment, AI Design, AI Development, Operaton and Monitoring**|


|GOVERN 4.2: Organizational teams document the risks and potential impacts of the AI technology they design, develop, deploy,<br>evaluate, and use, and they communicate about the impacts more broadly.|Col2|Col3|
|---|---|---|
|**Acton ID**|**Suggested Acton**|**GAI Risks**|
|GV-4.2-001|Establish terms of use and terms of service for GAI systems.|Intellectual Property; Dangerous,<br>Violent, or Hateful Content;<br>Obscene, Degrading, and/or<br>Abusive Content|
|GV-4.2-002|Include relevant AI Actors in the GAI system risk identﬁcaton process.|Human-AI Conﬁguraton|
|GV-4.2-003|Verify that downstream GAI system impacts (such as the use of third-party<br>plugins) are included in the impact documentaton process.|Value Chain and Component<br>Integraton|
|**AI Actor Tasks: AI Deployment, AI Design, AI Development, Operaton and Monitoring**|**AI Actor Tasks: AI Deployment, AI Design, AI Development, Operaton and Monitoring**|**AI Actor Tasks: AI Deployment, AI Design, AI Development, Operaton and Monitoring**|


|GOVERN 4.3: Organizational practices are in place to enable AI testing, identification of incidents, and information sharing.|Col2|Col3|
|---|---|---|
|**Acton ID**|**Suggested Acton**|**GAI Risks**|
|GV4.3--001|Establish policies for measuring the eﬀectveness of employed content<br>provenance methodologies (e.g., cryptography, watermarking, steganography,<br>etc.)|Informaton Integrity|
|GV-4.3-002|Establish organizatonal practces to identfy the minimum set of criteria<br>necessary for GAI system incident reportng such as: System ID (auto-generated<br>most likely), Title, Reporter, System/Source, Data Reported, Date of Incident,<br>Descripton, Impact(s), Stakeholder(s) Impacted.|Informaton Security|


19


|GV-4.3-003|Verify information sharing and feedback mechanisms among individuals and<br>organizations regarding any negative impact from GAI systems.|Information Integrity; Data<br>Privacy|
|---|---|---|
|**AI Actor Tasks: AI Impact Assessment, Aﬀected Individuals and Communites, Governance and Oversight**|**AI Actor Tasks: AI Impact Assessment, Aﬀected Individuals and Communites, Governance and Oversight**|**AI Actor Tasks: AI Impact Assessment, Aﬀected Individuals and Communites, Governance and Oversight**|


|GOVERN 5.1: Organizational policies and practices are in place to collect, consider, prioritize, and integrate feedback from those<br>external to the team that developed or deployed the AI system regarding the potential individual and societal impacts related to AI<br>risks.|Col2|Col3|
|---|---|---|
|**Acton ID**|**Suggested Acton**|**GAI Risks**|
|GV-5.1-001|Allocate tme and resources for outreach, feedback, and recourse processes in GAI<br>system development.|Human-AI Conﬁguraton; Harmful<br>Bias and Homogenizaton|
|GV-5.1-002|Document interactons with GAI systems to users prior to interactve actvites,<br>partcularly in contexts involving more signiﬁcant risks.|Human-AI Conﬁguraton;<br>Confabulaton|
|**AI Actor Tasks: AI Design, AI Impact Assessment, Aﬀected Individuals and Communites, Governance and Oversight**|**AI Actor Tasks: AI Design, AI Impact Assessment, Aﬀected Individuals and Communites, Governance and Oversight**|**AI Actor Tasks: AI Design, AI Impact Assessment, Aﬀected Individuals and Communites, Governance and Oversight**|


|GOVERN 6.1: Policies and procedures are in place that address AI risks associated with third-party entities, including risks of<br>infringement of a third-party’s intellectual property or other rights.|Col2|Col3|
|---|---|---|
|**Acton ID**|**Suggested Acton**|**GAI Risks**|
|GV-6.1-001|Categorize diﬀerent types of GAI content with associated third-party rights (e.g.,<br>copyright, intellectual property, data privacy).|Data Privacy; Intellectual<br>Property; Value Chain and<br>Component Integraton|
|GV-6.1-002|Conduct joint educatonal actvites and events in collaboraton with third partes<br>to promote best practces for managing GAI risks.|Value Chain and Component<br>Integraton|
|GV-6.1-003|Develop and validate approaches for measuring the success of content<br>provenance management eﬀorts with third partes (e.g., incidents detected and<br>response tmes).|Informaton Integrity; Value Chain<br>and Component Integraton|
|GV-6.1-004|Draf and maintain well-deﬁned contracts and service level agreements (SLAs)<br>that specify content ownership, usage rights, quality standards, security<br>requirements, and content provenance expectatons for GAI systems.|Informaton Integrity; Informaton<br>Security; Intellectual Property|


20


|GV-6.1-005|Implement a use-cased based supplier risk assessment framework to evaluate and<br>monitor third-party entities’ performance and adherence to content provenance<br>standards and technologies to detect anomalies and unauthorized changes;<br>services acquisition and value chain risk management; and legal compliance.|Data Privacy; Information<br>Integrity; Information Security;<br>Intellectual Property; Value Chain<br>and Component Integration|
|---|---|---|
|GV-6.1-006|Include clauses in contracts which allow an organizaton to evaluate third-party<br>GAI processes and standards.|Informaton Integrity|
|GV-6.1-007|Inventory all third-party enttes with access to organizatonal content and<br>establish approved GAI technology and service provider lists.|Value Chain and Component<br>Integraton|
|GV-6.1-008|Maintain records of changes to content made by third partes to promote content<br>provenance, including sources, tmestamps, metadata.|Informaton Integrity; Value Chain<br>and Component Integraton;<br>Intellectual Property|
|GV-6.1-009|Update and integrate due diligence processes for GAI acquisiton and<br>procurement vendor assessments to include intellectual property, data privacy,<br>security, and other risks. For example, update processes to: Address solutons that<br>may rely on embedded GAI technologies; Address ongoing monitoring,<br>assessments, and alertng, dynamic risk assessments, and real-tme reportng<br>tools for monitoring third-party GAI risks; Consider policy adjustments across GAI<br>modeling libraries, tools and APIs, ﬁne-tuned models, and embedded tools;<br>Assess GAI vendors, open-source or proprietary GAI tools, or GAI service<br>providers against incident or vulnerability databases.|Data Privacy; Human-AI<br>Conﬁguraton; Informaton<br>Security; Intellectual Property;<br>Value Chain and Component<br>Integraton; Harmful Bias and<br>Homogenizaton|
|GV-6.1-010|Update GAI acceptable use policies to address proprietary and open-source GAI<br>technologies and data, and contractors, consultants, and other third-party<br>personnel.|Intellectual Property; Value Chain<br>and Component Integraton|
|**AI Actor Tasks: Operaton and Monitoring, Procurement, Third-party enttes**|**AI Actor Tasks: Operaton and Monitoring, Procurement, Third-party enttes**|**AI Actor Tasks: Operaton and Monitoring, Procurement, Third-party enttes**|


|GOVERN 6.2: Contingency processes are in place to handle failures or incidents in third-party data or AI systems deemed to be<br>high-risk.|Col2|Col3|
|---|---|---|
|**Acton ID**|**Suggested Acton**|**GAI Risks**|
|GV-6.2-001|Document GAI risks associated with system value chain to identfy over-reliance<br>on third-party data and to identfy fallbacks.|Value Chain and Component<br>Integraton|
|GV-6.2-002|Document incidents involving third-party GAI data and systems, including open-<br>data and open-source sofware.|Intellectual Property; Value Chain<br>and Component Integraton|


21


|GV-6.2-003|Establish incident response plans for third-party GAI technologies: Align incident<br>response plans with impacts enumerated in MAP 5.1; Communicate third-party<br>GAI incident response plans to all relevant AI Actors; Define ownership of GAI<br>incident response functions; Rehearse third-party GAI incident response plans at<br>a regular cadence; Improve incident response plans based on retrospective<br>learning; Review incident response plans for alignment with relevant breach<br>reporting, data protection, data privacy, or other laws.|Data Privacy; Human-AI<br>Configuration; Information<br>Security; Value Chain and<br>Component Integration; Harmful<br>Bias and Homogenization|
|---|---|---|
|GV-6.2-004|Establish policies and procedures for contnuous monitoring of third-party GAI<br>systems in deployment.|Value Chain and Component<br>Integraton|
|GV-6.2-005|Establish policies and procedures that address GAI data redundancy, including<br>model weights and other system artfacts.|Harmful Bias and Homogenizaton|
|GV-6.2-006|Establish policies and procedures to test and manage risks related to rollover and<br>fallback technologies for GAI systems, acknowledging that rollover and fallback<br>may include manual processing.|Informaton Integrity|
|GV-6.2-007|Review vendor contracts and avoid arbitrary or capricious terminaton of critcal<br>GAI technologies or vendor services and non-standard terms that may amplify or<br>defer liability in unexpected ways and/or contribute to unauthorized data<br>collecton by vendors or third-partes (e.g., secondary data use). Consider: Clear<br>assignment of liability and responsibility for incidents, GAI system changes over<br>tme (e.g., ﬁne-tuning, drif, decay); Request: Notﬁcaton and disclosure for<br>serious incidents arising from third-party data and systems; Service Level<br>Agreements (SLAs) in vendor contracts that address incident response, response<br>tmes, and availability of critcal support.|Human-AI Conﬁguraton;<br>Informaton Security; Value Chain<br>and Component Integraton|
|**AI Actor Tasks: AI Deployment, Operaton and Monitoring, TEVV, Third-party enttes**|**AI Actor Tasks: AI Deployment, Operaton and Monitoring, TEVV, Third-party enttes**|**AI Actor Tasks: AI Deployment, Operaton and Monitoring, TEVV, Third-party enttes**|


|MAP 1.1: Intended purposes, potentially beneficial uses, context specific laws, norms and expectations, and prospective settings in<br>which the AI system will be deployed are understood and documented. Considerations include: the specific set or types of users<br>along with their expectations; potential positive and negative impacts of system uses to individuals, communities, organizations,<br>society, and the planet; assumptions and related limitations about AI system purposes, uses, and risks across the development or<br>product AI lifecycle; and related TEVV and system metrics.|Col2|Col3|
|---|---|---|
|**Acton ID**|**Suggested Acton**|**GAI Risks**|
|MP-1.1-001|When identfying intended purposes, consider factors such as internal vs.<br>external use, narrow vs. broad applicaton scope, ﬁne-tuning, and varietes of<br>data sources (e.g., grounding, retrieval-augmented generaton).|Data Privacy; Intellectual<br>Property|


22


|MP-1.1-002|Determine and document the expected and acceptable GAI system context of<br>use in collaboration with socio-cultural and other domain experts, by assessing:<br>Assumptions and limitations; Direct value to the organization; Intended<br>operational environment and observed usage patterns; Potential positive and<br>negative impacts to individuals, public safety, groups, communities,<br>organizations, democratic institutions, and the physical environment; Social<br>norms and expectations.|Harmful Bias and Homogenization|
|---|---|---|
|MP-1.1-003|Document risk measurement plans to address identﬁed risks. Plans may<br>include, as applicable: Individual and group cognitve biases (e.g., conﬁrmaton<br>bias, funding bias, groupthink) for AI Actors involved in the design,<br>implementaton, and use of GAI systems; Known past GAI system incidents and<br>failure modes; In-context use and foreseeable misuse, abuse, and oﬀ-label use;<br>Over reliance on quanttatve metrics and methodologies without suﬃcient<br>awareness of their limitatons in the context(s) of use; Standard measurement<br>and structured human feedback approaches; Antcipated human-AI<br>conﬁguratons.|Human-AI Conﬁguraton; Harmful<br>Bias and Homogenizaton;<br>Dangerous, Violent, or Hateful<br>Content|
|MP-1.1-004|Identfy and document foreseeable illegal uses or applicatons of the GAI system<br>that surpass organizatonal risk tolerances.|CBRN Informaton or Capabilites;<br>Dangerous, Violent, or Hateful<br>Content; Obscene, Degrading,<br>and/or Abusive Content|
|**AI Actor Tasks: AI Deployment**|**AI Actor Tasks: AI Deployment**|**AI Actor Tasks: AI Deployment**|


|MAP 1.2: Interdisciplinary AI Actors, competencies, skills, and capacities for establishing context reflect demographic diversity and<br>broad domain and user experience expertise, and their participation is documented. Opportunities for interdisciplinary<br>collaboration are prioritized.|Col2|Col3|
|---|---|---|
|**Acton ID**|**Suggested Acton**|**GAI Risks**|
|MP-1.2-001|Establish and empower interdisciplinary teams that reﬂect a wide range of<br>capabilites, competencies, demographic groups, domain expertse, educatonal<br>backgrounds, lived experiences, professions, and skills across the enterprise to<br>inform and conduct risk measurement and management functons.|Human-AI Conﬁguraton; Harmful<br>Bias and Homogenizaton|
|MP-1.2-002|Verify that data or benchmarks used in risk measurement, and users,<br>partcipants, or subjects involved in structured GAI public feedback exercises<br>are representatve of diverse in-context user populatons.|Human-AI Conﬁguraton; Harmful<br>Bias and Homogenizaton|
|**AI Actor Tasks: AI Deployment**|**AI Actor Tasks: AI Deployment**|**AI Actor Tasks: AI Deployment**|


23


|MAP 2.1: The specific tasks and methods used to implement the tasks that the AI system will support are defined (e.g., classifiers,<br>generative models, recommenders).|Col2|Col3|
|---|---|---|
|**Acton ID**|**Suggested Acton**|**GAI Risks**|
|MP-2.1-001|Establish known assumptons and practces for determining data origin and<br>content lineage, for documentaton and evaluaton purposes.|Informaton Integrity|
|MP-2.1-002|Insttute test and evaluaton for data and content ﬂows within the GAI system,<br>including but not limited to, original data sources, data transformatons, and<br>decision-making criteria.|Intellectual Property; Data Privacy|
|**AI Actor Tasks: TEVV**|**AI Actor Tasks: TEVV**|**AI Actor Tasks: TEVV**|


|MAP 2.2: Information about the AI system’s knowledge limits and how system output may be utilized and overseen by humans is<br>documented. Documentation provides sufficient information to assist relevant AI Actors when making decisions and taking<br>subsequent actions.|Col2|Col3|
|---|---|---|
|**Acton ID**|**Suggested Acton**|**GAI Risks**|
|MP-2.2-001|Identfy and document how the system relies on upstream data sources,<br>including for content provenance, and if it serves as an upstream dependency for<br>other systems.|Informaton Integrity; Value Chain<br>and Component Integraton|
|MP-2.2-002|Observe and analyze how the GAI system interacts with external networks, and<br>identfy any potental for negatve externalites, partcularly where content<br>provenance might be compromised.|Informaton Integrity|
|**AI Actor Tasks: End Users**|**AI Actor Tasks: End Users**|**AI Actor Tasks: End Users**|


|MAP 2.3: Scientific integrity and TEVV considerations are identified and documented, including those related to experimental<br>design, data collection and selection (e.g., availability, representativeness, suitability), system trustworthiness, and construct<br>validation|Col2|Col3|
|---|---|---|
|**Acton ID**|**Suggested Acton**|**GAI Risks**|
|MP-2.3-001|Assess the accuracy, quality, reliability, and authentcity of GAI output by<br>comparing it to a set of known ground truth data and by using a variety of<br>evaluaton methods (e.g., human oversight and automated evaluaton, proven<br>cryptographic techniques, review of content inputs).|Informaton Integrity|


24


|MP-2.3-002|Review and document accuracy, representativeness, relevance, suitability of data<br>used at different stages of AI life cycle.|Harmful Bias and Homogenization;<br>Intellectual Property|
|---|---|---|
|MP-2.3-003|Deploy and document fact-checking techniques to verify the accuracy and<br>veracity of informaton generated by GAI systems, especially when the<br>informaton comes from multple (or unknown) sources.|Informaton Integrity|
|MP-2.3-004|Develop and implement testng techniques to identfy GAI produced content (e.g.,<br>synthetc media) that might be indistnguishable from human-generated content.|Informaton Integrity|
|MP-2.3-005|Implement plans for GAI systems to undergo regular adversarial testng to identfy<br>vulnerabilites and potental manipulaton or misuse.|Informaton Security|
|**AI Actor Tasks: AI Development, Domain Experts, TEVV**|**AI Actor Tasks: AI Development, Domain Experts, TEVV**|**AI Actor Tasks: AI Development, Domain Experts, TEVV**|


|MAP 3.4: Processes for operator and practitioner proficiency with AI system performance and trustworthiness – and relevant<br>technical standards and certifications – are defined, assessed, and documented.|Col2|Col3|
|---|---|---|
|**Acton ID**|**Suggested Acton**|**GAI Risks**|
|MP-3.4-001|Evaluate whether GAI operators and end-users can accurately understand<br>content lineage and origin.|Human-AI Conﬁguraton;<br>Informaton Integrity|
|MP-3.4-002|Adapt existng training programs to include modules on digital content<br>transparency.|Informaton Integrity|
|MP-3.4-003|Develop certﬁcaton programs that test proﬁciency in managing GAI risks and<br>interpretng content provenance, relevant to speciﬁc industry and context.|Informaton Integrity|
|MP-3.4-004|Delineate human proﬁciency tests from tests of GAI capabilites.|Human-AI Conﬁguraton|
|MP-3.4-005|Implement systems to contnually monitor and track the outcomes of human-GAI<br>conﬁguratons for future reﬁnement and improvements.|Human-AI Conﬁguraton;<br>Informaton Integrity|
|MP-3.4-006|Involve the end-users, practtoners, and operators in GAI system in prototyping<br>and testng actvites. Make sure these tests cover various scenarios, such as crisis<br>situatons or ethically sensitve contexts.|Human-AI Conﬁguraton;<br>Informaton Integrity; Harmful Bias<br>and Homogenizaton; Dangerous,<br>Violent, or Hateful Content|
|**AI Actor Tasks: AI Design, AI Development, Domain Experts, End-Users, Human Factors, Operaton and Monitoring**|**AI Actor Tasks: AI Design, AI Development, Domain Experts, End-Users, Human Factors, Operaton and Monitoring**|**AI Actor Tasks: AI Design, AI Development, Domain Experts, End-Users, Human Factors, Operaton and Monitoring**|


25


|MAP 4.1: Approaches for mapping AI technology and legal risks of its components – including the use of third-party data or<br>software – are in place, followed, and documented, as are risks of infringement of a third-party’s intellectual property or other<br>rights.|Col2|Col3|
|---|---|---|
|**Acton ID**|**Suggested Acton**|**GAI Risks**|
|MP-4.1-001|Conduct periodic monitoring of AI-generated content for privacy risks; address any<br>possible instances of PII or sensitve data exposure.|Data Privacy|
|MP-4.1-002|Implement processes for responding to potental intellectual property infringement<br>claims or other rights.|Intellectual Property|
|MP-4.1-003|Connect new GAI policies, procedures, and processes to existng model, data,<br>sofware development, and IT governance and to legal, compliance, and risk<br>management actvites.|Informaton Security; Data Privacy|
|MP-4.1-004|Document training data curaton policies, to the extent possible and according to<br>applicable laws and policies.|Intellectual Property; Data Privacy;<br>Obscene, Degrading, and/or<br>Abusive Content|
|MP-4.1-005|Establish policies for collecton, retenton, and minimum quality of data, in<br>consideraton of the following risks: Disclosure of inappropriate CBRN informaton;<br>Use of Illegal or dangerous content; Oﬀensive cyber capabilites; Training data<br>imbalances that could give rise to harmful biases; Leak of personally identﬁable<br>informaton, including facial likenesses of individuals.|CBRN Informaton or Capabilites;<br>Intellectual Property; Informaton<br>Security; Harmful Bias and<br>Homogenizaton; Dangerous,<br>Violent, or Hateful Content; Data<br>Privacy|
|MP-4.1-006|Implement policies and practces deﬁning how third-party intellectual property and<br>training data will be used, stored, and protected.|Intellectual Property; Value Chain<br>and Component Integraton|
|MP-4.1-007|Re-evaluate models that were ﬁne-tuned or enhanced on top of third-party<br>models.|Value Chain and Component<br>Integraton|
|MP-4.1-008|Re-evaluate risks when adaptng GAI models to new domains. Additonally,<br>establish warning systems to determine if a GAI system is being used in a new<br>domain where previous assumptons (relatng to context of use or mapped risks<br>such as security, and safety) may no longer hold.|CBRN Informaton or Capabilites;<br>Intellectual Property; Harmful Bias<br>and Homogenizaton; Dangerous,<br>Violent, or Hateful Content; Data<br>Privacy|
|MP-4.1-009|Leverage approaches to detect the presence of PII or sensitve data in generated<br>output text, image, video, or audio.|Data Privacy|


26


|MP-4.1-010|Conduct appropriate diligence on training data use to assess intellectual property,<br>and privacy, risks, including to examine whether use of proprietary or sensitive<br>training data is consistent with applicable laws.|Intellectual Property; Data Privacy|
|---|---|---|
|**AI Actor Tasks: Governance and Oversight, Operaton and Monitoring, Procurement, Third-party enttes**|**AI Actor Tasks: Governance and Oversight, Operaton and Monitoring, Procurement, Third-party enttes**|**AI Actor Tasks: Governance and Oversight, Operaton and Monitoring, Procurement, Third-party enttes**|


|MAP 5.1: Likelihood and magnitude of each identified impact (both potentially beneficial and harmful) based on expected use, past<br>uses of AI systems in similar contexts, public incident reports, feedback from those external to the team that developed or deployed<br>the AI system, or other data are identified and documented.|Col2|Col3|
|---|---|---|
|**Acton ID**|**Suggested Acton**|**GAI Risks**|
|MP-5.1-001|Apply TEVV practces for content provenance (e.g., probing a system's synthetc<br>data generaton capabilites for potental misuse or vulnerabilites.|Informaton Integrity; Informaton<br>Security|
|MP-5.1-002|Identfy potental content provenance harms of GAI, such as misinformaton or<br>disinformaton, deepfakes, including NCII, or tampered content. Enumerate and<br>rank risks based on their likelihood and potental impact, and determine how well<br>provenance solutons address speciﬁc risks and/or harms.|Informaton Integrity; Dangerous,<br>Violent, or Hateful Content;<br>Obscene, Degrading, and/or<br>Abusive Content|
|MP-5.1-003|Consider disclosing use of GAI to end users in relevant contexts, while considering<br>the objectve of disclosure, the context of use, the likelihood and magnitude of the<br>risk posed, the audience of the disclosure, as well as the frequency of the<br>disclosures.|Human-AI Conﬁguraton|
|MP-5.1-004|Prioritze GAI structured public feedback processes based on risk assessment<br>estmates.|Informaton Integrity; CBRN<br>Informaton or Capabilites;<br>Dangerous, Violent, or Hateful<br>Content; Harmful Bias and<br>Homogenizaton|
|MP-5.1-005|Conduct adversarial role-playing exercises, GAI red-teaming, or chaos testng to<br>identfy anomalous or unforeseen failure modes.|Informaton Security|
|MP-5.1-006|Proﬁle threats and negatve impacts arising from GAI systems interactng with,<br>manipulatng, or generatng content, and outlining known and potental<br>vulnerabilites and the likelihood of their occurrence.|Informaton Security|
|**AI Actor Tasks: AI Deployment, AI Design, AI Development, AI Impact Assessment, Aﬀected Individuals and Communites, End-**<br>**Users, Operaton and Monitoring**|**AI Actor Tasks: AI Deployment, AI Design, AI Development, AI Impact Assessment, Aﬀected Individuals and Communites, End-**<br>**Users, Operaton and Monitoring**|**AI Actor Tasks: AI Deployment, AI Design, AI Development, AI Impact Assessment, Aﬀected Individuals and Communites, End-**<br>**Users, Operaton and Monitoring**|


27


|MAP 5.2: Practices and personnel for supporting regular engagement with relevant AI Actors and integrating feedback about<br>positive, negative, and unanticipated impacts are in place and documented.|Col2|Col3|
|---|---|---|
|**Acton ID**|**Suggested Acton**|**GAI Risks**|
|MP-5.2-001|Determine context-based measures to identfy if new impacts are present due to<br>the GAI system, including regular engagements with downstream AI Actors to<br>identfy and quantfy new contexts of unantcipated impacts of GAI systems.|Human-AI Conﬁguraton; Value<br>Chain and Component Integraton|
|MP-5.2-002|Plan regular engagements with AI Actors responsible for inputs to GAI systems,<br>including third-party data and algorithms, to review and evaluate unantcipated<br>impacts.|Human-AI Conﬁguraton; Value<br>Chain and Component Integraton|
|**AI Actor Tasks: AI Deployment, AI Design, AI Impact Assessment, Aﬀected Individuals and Communites, Domain Experts, End-**<br>**Users, Human Factors, Operaton and Monitoring**|**AI Actor Tasks: AI Deployment, AI Design, AI Impact Assessment, Aﬀected Individuals and Communites, Domain Experts, End-**<br>**Users, Human Factors, Operaton and Monitoring**|**AI Actor Tasks: AI Deployment, AI Design, AI Impact Assessment, Aﬀected Individuals and Communites, Domain Experts, End-**<br>**Users, Human Factors, Operaton and Monitoring**|


|MEASURE 1.1: Approaches and metrics for measurement of AI risks enumerated during the MAP function are selected for<br>implementation starting with the most significant AI risks. The risks or trustworthiness characteristics that will not – or cannot – be<br>measured are properly documented.|Col2|Col3|
|---|---|---|
|**Acton ID**|**Suggested Acton**|**GAI Risks**|
|MS-1.1-001|Employ methods to trace the origin and modiﬁcatons of digital content.|Informaton Integrity|
|MS-1.1-002|Integrate tools designed to analyze content provenance and detect data<br>anomalies, verify the authentcity of digital signatures, and identfy paterns<br>associated with misinformaton or manipulaton.|Informaton Integrity|
|MS-1.1-003|Disaggregate evaluaton metrics by demographic factors to identfy any<br>discrepancies in how content provenance mechanisms work across diverse<br>populatons.|Informaton Integrity; Harmful<br>Bias and Homogenizaton|
|MS-1.1-004|Develop a suite of metrics to evaluate structured public feedback exercises<br>informed by representatve AI Actors.|Human-AI Conﬁguraton; Harmful<br>Bias and Homogenizaton; CBRN<br>Informaton or Capabilites|
|MS-1.1-005|Evaluate novel methods and technologies for the measurement of GAI-related<br>risks including in content provenance, oﬀensive cyber, and CBRN, while<br>maintaining the models’ ability to produce valid, reliable, and factually accurate<br>outputs.|Informaton Integrity; CBRN<br>Informaton or Capabilites;<br>Obscene, Degrading, and/or<br>Abusive Content|


28


|MS-1.1-006|Implement continuous monitoring of GAI system impacts to identify whether GAI<br>outputs are equitable across various sub-populations. Seek active and direct<br>feedback from affected communities via structured feedback mechanisms or red-<br>teaming to monitor and improve outputs.|Harmful Bias and Homogenization|
|---|---|---|
|MS-1.1-007|Evaluate the quality and integrity of data used in training and the provenance of<br>AI-generated content, for example by employing techniques like chaos<br>engineering and seeking stakeholder feedback.|Informaton Integrity|
|MS-1.1-008|Deﬁne use cases, contexts of use, capabilites, and negatve impacts where<br>structured human feedback exercises, e.g., GAI red-teaming, would be most<br>beneﬁcial for GAI risk measurement and management based on the context of<br>use.|Harmful Bias and<br>Homogenizaton; CBRN<br>Informaton or Capabilites|
|MS-1.1-009|Track and document risks or opportunites related to all GAI risks that cannot be<br>measured quanttatvely, including explanatons as to why some risks cannot be<br>measured (e.g., due to technological limitatons, resource constraints, or<br>trustworthy consideratons). Include unmeasured risks in marginal risks.|Informaton Integrity|
|**AI Actor Tasks: AI Development, Domain Experts, TEVV**|**AI Actor Tasks: AI Development, Domain Experts, TEVV**|**AI Actor Tasks: AI Development, Domain Experts, TEVV**|


|MEASURE 1.3: Internal experts who did not serve as front-line developers for the system and/or independent assessors are<br>involved in regular assessments and updates. Domain experts, users, AI Actors external to the team that developed or deployed the<br>AI system, and affected communities are consulted in support of assessments as necessary per organizational risk tolerance.|Col2|Col3|
|---|---|---|
|**Acton ID**|**Suggested Acton**|**GAI Risks**|
|MS-1.3-001|Deﬁne relevant groups of interest (e.g., demographic groups, subject mater<br>experts, experience with GAI technology) within the context of use as part of<br>plans for gathering structured public feedback.|Human-AI Conﬁguraton; Harmful<br>Bias and Homogenizaton; CBRN<br>Informaton or Capabilites|
|MS-1.3-002|Engage in internal and external evaluatons, GAI red-teaming, impact<br>assessments, or other structured human feedback exercises in consultaton<br>with representatve AI Actors with expertse and familiarity in the context of<br>use, and/or who are representatve of the populatons associated with the<br>context of use.|Human-AI Conﬁguraton; Harmful<br>Bias and Homogenizaton; CBRN<br>Informaton or Capabilites|
|MS-1.3-003|Verify those conductng structured human feedback exercises are not directly<br>involved in system development tasks for the same GAI model.|Human-AI Conﬁguraton; Data<br>Privacy|
|**AI Actor Tasks: AI Deployment, AI Development, AI Impact Assessment, Aﬀected Individuals and Communites, Domain Experts,**<br>**End-Users, Operaton and Monitoring, TEVV**|**AI Actor Tasks: AI Deployment, AI Development, AI Impact Assessment, Aﬀected Individuals and Communites, Domain Experts,**<br>**End-Users, Operaton and Monitoring, TEVV**|**AI Actor Tasks: AI Deployment, AI Development, AI Impact Assessment, Aﬀected Individuals and Communites, Domain Experts,**<br>**End-Users, Operaton and Monitoring, TEVV**|


29


|MEASURE 2.2: Evaluations involving human subjects meet applicable requirements (including human subject protection) and are<br>representative of the relevant population.|Col2|Col3|
|---|---|---|
|**Acton ID**|**Suggested Acton**|**GAI Risks**|
|MS-2.2-001|Assess and manage statstcal biases related to GAI content provenance through<br>techniques such as re-sampling, re-weightng, or adversarial training.|Informaton Integrity; Informaton<br>Security; Harmful Bias and<br>Homogenizaton|
|MS-2.2-002|Document how content provenance data is tracked and how that data interacts<br>with privacy and security. Consider: Anonymizing data to protect the privacy of<br>human subjects; Leveraging privacy output ﬁlters; Removing any personally<br>identﬁable informaton (PII) to prevent potental harm or misuse.|Data Privacy; Human AI<br>Conﬁguraton; Informaton<br>Integrity; Informaton Security;<br>Dangerous, Violent, or Hateful<br>Content|
|MS-2.2-003|Provide human subjects with optons to withdraw partcipaton or revoke their<br>consent for present or future use of their data in GAI applicatons.|Data Privacy; Human-AI<br>Conﬁguraton; Informaton<br>Integrity|
|MS-2.2-004|Use techniques such as anonymizaton, diﬀerental privacy or other privacy-<br>enhancing technologies to minimize the risks associated with linking AI-generated<br>content back to individual human subjects.|Data Privacy; Human-AI<br>Conﬁguraton|
|**AI Actor Tasks: AI Development, Human Factors, TEVV**|**AI Actor Tasks: AI Development, Human Factors, TEVV**|**AI Actor Tasks: AI Development, Human Factors, TEVV**|


|MEASURE 2.3: AI system performance or assurance criteria are measured qualitatively or quantitatively and demonstrated for<br>conditions similar to deployment setting(s). Measures are documented.|Col2|Col3|
|---|---|---|
|**Acton ID**|**Suggested Acton**|**GAI Risks**|
|MS-2.3-001|Consider baseline model performance on suites of benchmarks when selectng a<br>model for ﬁne tuning or enhancement with retrieval-augmented generaton.|Informaton Security;<br>Confabulaton|
|MS-2.3-002|Evaluate claims of model capabilites using empirically validated methods.|Confabulaton; Informaton<br>Security|
|MS-2.3-003|Share results of pre-deployment testng with relevant GAI Actors, such as those<br>with system release approval authority.|Human-AI Conﬁguraton|


30


|MS-2.3-004|Utilize a purpose-built testing environment such as NIST Dioptra to empirically<br>evaluate GAI trustworthy characteristics.|CBRN Information or Capabilities;<br>Data Privacy; Confabulation;<br>Information Integrity; Information<br>Security; Dangerous, Violent, or<br>Hateful Content; Harmful Bias and<br>Homogenization|
|---|---|---|
|**AI Actor Tasks: AI Deployment, TEVV**|**AI Actor Tasks: AI Deployment, TEVV**|**AI Actor Tasks: AI Deployment, TEVV**|


|MEASURE 2.5: The AI system to be deployed is demonstrated to be valid and reliable. Limitations of the generalizability beyond the<br>conditions under which the technology was developed are documented.|Col2|Col3|
|---|---|---|
|**Acton ID**|**Suggested Acton**|**Risks**|
|MS-2.5-001|Avoid extrapolatng GAI system performance or capabilites from narrow, non-<br>systematc, and anecdotal assessments.|Human-AI Conﬁguraton;<br>Confabulaton|
|MS-2.5-002|Document the extent to which human domain knowledge is employed to<br>improve GAI system performance, via, e.g., RLHF, ﬁne-tuning, retrieval-<br>augmented generaton, content moderaton, business rules.|Human-AI Conﬁguraton|
|MS-2.5-003|Review and verify sources and citatons in GAI system outputs during pre-<br>deployment risk measurement and ongoing monitoring actvites.|Confabulaton|
|MS-2.5-004|Track and document instances of anthropomorphizaton (e.g., human images,<br>mentons of human feelings, cyborg imagery or motfs) in GAI system interfaces.|Human-AI Conﬁguraton|
|MS-2.5-005|Verify GAI system training data and TEVV data provenance, and that ﬁne-tuning<br>or retrieval-augmented generaton data is grounded.|Informaton Integrity|
|MS-2.5-006|Regularly review security and safety guardrails, especially if the GAI system is<br>being operated in novel circumstances. This includes reviewing reasons why the<br>GAI system was initally assessed as being safe to deploy.|Informaton Security; Dangerous,<br>Violent, or Hateful Content|
|**AI Actor Tasks: Domain Experts, TEVV**|**AI Actor Tasks: Domain Experts, TEVV**|**AI Actor Tasks: Domain Experts, TEVV**|


31


|MEASURE 2.6: The AI system is evaluated regularly for safety risks – as identified in the MAP function. The AI system to be<br>deployed is demonstrated to be safe, its residual negative risk does not exceed the risk tolerance, and it can fail safely, particularly if<br>made to operate beyond its knowledge limits. Safety metrics reflect system reliability and robustness, real-time monitoring, and<br>response times for AI system failures.|Col2|Col3|
|---|---|---|
|**Acton ID**|**Suggested Acton**|**GAI Risks**|
|MS-2.6-001|Assess adverse impacts, including health and wellbeing impacts for value chain<br>or other AI Actors that are exposed to sexually explicit, oﬀensive, or violent<br>informaton during GAI training and maintenance.|Human-AI Conﬁguraton; Obscene,<br>Degrading, and/or Abusive<br>Content; Value Chain and<br>Component Integraton;<br>Dangerous, Violent, or Hateful<br>Content|
|MS-2.6-002|Assess existence or levels of harmful bias, intellectual property infringement,<br>data privacy violatons, obscenity, extremism, violence, or CBRN informaton in<br>system training data.|Data Privacy; Intellectual Property;<br>Obscene, Degrading, and/or<br>Abusive Content; Harmful Bias and<br>Homogenizaton; Dangerous,<br>Violent, or Hateful Content; CBRN<br>Informaton or Capabilites|
|MS-2.6-003|Re-evaluate safety features of ﬁne-tuned models when the negatve risk exceeds<br>organizatonal risk tolerance.|Dangerous, Violent, or Hateful<br>Content|
|MS-2.6-004|Review GAI system outputs for validity and safety: Review generated code to<br>assess risks that may arise from unreliable downstream decision-making.|Value Chain and Component<br>Integraton; Dangerous, Violent, or<br>Hateful Content|
|MS-2.6-005|Verify that GAI system architecture can monitor outputs and performance, and<br>handle, recover from, and repair errors when security anomalies, threats and<br>impacts are detected.|Confabulaton; Informaton<br>Integrity; Informaton Security|
|MS-2.6-006|Verify that systems properly handle queries that may give rise to inappropriate,<br>malicious, or illegal usage, including facilitatng manipulaton, extorton, targeted<br>impersonaton, cyber-atacks, and weapons creaton.|CBRN Informaton or Capabilites;<br>Informaton Security|
|MS-2.6-007|Regularly evaluate GAI system vulnerabilites to possible circumventon of safety<br>measures.|CBRN Informaton or Capabilites;<br>Informaton Security|
|**AI Actor Tasks: AI Deployment, AI Impact Assessment, Domain Experts, Operaton and Monitoring, TEVV**|**AI Actor Tasks: AI Deployment, AI Impact Assessment, Domain Experts, Operaton and Monitoring, TEVV**|**AI Actor Tasks: AI Deployment, AI Impact Assessment, Domain Experts, Operaton and Monitoring, TEVV**|


32


|MEASURE 2.7: AI system security and resilience – as identified in the MAP function – are evaluated and documented.|Col2|Col3|
|---|---|---|
|**Acton ID**|**Suggested Acton**|**GAI Risks**|
|MS-2.7-001|Apply established security measures to: Assess likelihood and magnitude of<br>vulnerabilites and threats such as backdoors, compromised dependencies, data<br>breaches, eavesdropping, man-in-the-middle atacks, reverse engineering,<br>autonomous agents, model thef or exposure of model weights, AI inference,<br>bypass, extracton, and other baseline security concerns.|Data Privacy; Informaton Integrity;<br>Informaton Security; Value Chain<br>and Component Integraton|
|MS-2.7-002|Benchmark GAI system security and resilience related to content provenance<br>against industry standards and best practces. Compare GAI system security<br>features and content provenance methods against industry state-of-the-art.|Informaton Integrity; Informaton<br>Security|
|MS-2.7-003|Conduct user surveys to gather user satsfacton with the AI-generated content<br>and user perceptons of content authentcity. Analyze user feedback to identfy<br>concerns and/or current literacy levels related to content provenance and<br>understanding of labels on content.|Human-AI Conﬁguraton;<br>Informaton Integrity|
|MS-2.7-004|Identfy metrics that reﬂect the eﬀectveness of security measures, such as data<br>provenance, the number of unauthorized access atempts, inference, bypass,<br>extracton, penetratons, or provenance veriﬁcaton.|Informaton Integrity; Informaton<br>Security|
|MS-2.7-005|Measure reliability of content authentcaton methods, such as watermarking,<br>cryptographic signatures, digital ﬁngerprints, as well as access controls,<br>conformity assessment, and model integrity veriﬁcaton, which can help support<br>the eﬀectve implementaton of content provenance techniques. Evaluate the<br>rate of false positves and false negatves in content provenance, as well as true<br>positves and true negatves for veriﬁcaton.|Informaton Integrity|
|MS-2.7-006|Measure the rate at which recommendatons from security checks and incidents<br>are implemented. Assess how quickly the AI system can adapt and improve<br>based on lessons learned from security incidents and feedback.|Informaton Integrity; Informaton<br>Security|
|MS-2.7-007|Perform AI red-teaming to assess resilience against: Abuse to facilitate atacks on<br>other systems (e.g., malicious code generaton, enhanced phishing content), GAI<br>atacks (e.g., prompt injecton), ML atacks (e.g., adversarial examples/prompts,<br>data poisoning, membership inference, model extracton, sponge examples).|Informaton Security; Harmful Bias<br>and Homogenizaton; Dangerous,<br>Violent, or Hateful Content|
|MS-2.7-008|Verify ﬁne-tuning does not compromise safety and security controls.|Informaton Integrity; Informaton<br>Security; Dangerous, Violent, or<br>Hateful Content|


33


|MS-2.7-009|Regularly assess and verify that security measures remain effective and have not<br>been compromised.|Information Security|
|---|---|---|
|**AI Actor Tasks: AI Deployment, AI Impact Assessment, Domain Experts, Operaton and Monitoring, TEVV**|**AI Actor Tasks: AI Deployment, AI Impact Assessment, Domain Experts, Operaton and Monitoring, TEVV**|**AI Actor Tasks: AI Deployment, AI Impact Assessment, Domain Experts, Operaton and Monitoring, TEVV**|


|MEASURE 2.8: Risks associated with transparency and accountability – as identified in the MAP function – are examined and<br>documented.|Col2|Col3|
|---|---|---|
|**Acton ID**|**Suggested Acton**|**GAI Risks**|
|MS-2.8-001|Compile statstcs on actual policy violatons, take-down requests, and intellectual<br>property infringement for organizatonal GAI systems: Analyze transparency<br>reports across demographic groups, languages groups.|Intellectual Property; Harmful Bias<br>and Homogenizaton|
|MS-2.8-002|Document the instructons given to data annotators or AI red-teamers.|Human-AI Conﬁguraton|
|MS-2.8-003|Use digital content transparency solutons to enable the documentaton of each<br>instance where content is generated, modiﬁed, or shared to provide a tamper-<br>proof history of the content, promote transparency, and enable traceability.<br>Robust version control systems can also be applied to track changes across the AI<br>lifecycle over tme.|Informaton Integrity|
|MS-2.8-004|Verify adequacy of GAI system user instructons through user testng.|Human-AI Conﬁguraton|
|**AI Actor Tasks: AI Deployment, AI Impact Assessment, Domain Experts, Operaton and Monitoring, TEVV**|**AI Actor Tasks: AI Deployment, AI Impact Assessment, Domain Experts, Operaton and Monitoring, TEVV**|**AI Actor Tasks: AI Deployment, AI Impact Assessment, Domain Experts, Operaton and Monitoring, TEVV**|


34


|MEASURE 2.9: The AI model is explained, validated, and documented, and AI system output is interpreted within its context – as<br>identified in the MAP function – to inform responsible use and governance.|Col2|Col3|
|---|---|---|
|**Acton ID**|**Suggested Acton**|**GAI Risks**|
|MS-2.9-001|Apply and document ML explanaton results such as: Analysis of embeddings,<br>Counterfactual prompts, Gradient-based atributons, Model<br>compression/surrogate models, Occlusion/term reducton.|Confabulaton|
|MS-2.9-002|Document GAI model details including: Proposed use and organizatonal value;<br>Assumptons and limitatons, Data collecton methodologies; Data provenance;<br>Data quality; Model architecture (e.g., convolutonal neural network,<br>transformers, etc.); Optmizaton objectves; Training algorithms; RLHF<br>approaches; Fine-tuning or retrieval-augmented generaton approaches;<br>Evaluaton data; Ethical consideratons; Legal and regulatory requirements.|Informaton Integrity; Harmful Bias<br>and Homogenizaton|
|**AI Actor Tasks: AI Deployment, AI Impact Assessment, Domain Experts, End-Users, Operaton and Monitoring, TEVV**|**AI Actor Tasks: AI Deployment, AI Impact Assessment, Domain Experts, End-Users, Operaton and Monitoring, TEVV**|**AI Actor Tasks: AI Deployment, AI Impact Assessment, Domain Experts, End-Users, Operaton and Monitoring, TEVV**|


|MEASURE 2.10: Privacy risk of the AI system – as identified in the MAP function – is examined and documented.|Col2|Col3|
|---|---|---|
|**Acton ID**|**Suggested Acton**|**GAI Risks**|
|MS-2.10-001|Conduct AI red-teaming to assess issues such as: Outputng of training data<br>samples, and subsequent reverse engineering, model extracton, and<br>membership inference risks; Revealing biometric, conﬁdental, copyrighted,<br>licensed, patented, personal, proprietary, sensitve, or trade-marked informaton;<br>Tracking or revealing locaton informaton of users or members of training<br>datasets.|Human-AI Conﬁguraton;<br>Informaton Integrity; Intellectual<br>Property|
|MS-2.10-002|Engage directly with end-users and other stakeholders to understand their<br>expectatons and concerns regarding content provenance. Use this feedback to<br>guide the design of provenance data-tracking techniques.|Human-AI Conﬁguraton;<br>Informaton Integrity|
|MS-2.10-003|Verify deduplicaton of GAI training data samples, partcularly regarding synthetc<br>data.|Harmful Bias and Homogenizaton|
|**AI Actor Tasks: AI Deployment, AI Impact Assessment, Domain Experts, End-Users, Operaton and Monitoring, TEVV**|**AI Actor Tasks: AI Deployment, AI Impact Assessment, Domain Experts, End-Users, Operaton and Monitoring, TEVV**|**AI Actor Tasks: AI Deployment, AI Impact Assessment, Domain Experts, End-Users, Operaton and Monitoring, TEVV**|


35


|MEASURE 2.11: Fairness and bias – as identified in the MAP function – are evaluated and results are documented.|Col2|Col3|
|---|---|---|
|**Acton ID**|**Suggested Acton**|**GAI Risks**|
|MS-2.11-001|Apply use-case appropriate benchmarks (e.g., Bias Benchmark Questons, Real<br>Hateful or Harmful Prompts,Winogender Schemas15) to quantfy systemic bias,<br>stereotyping, denigraton, and hateful content in GAI system outputs;<br>Document assumptons and limitatons of benchmarks, including any actual or<br>possible training/test data cross contaminaton, relatve to in-context<br>deployment environment.|Harmful Bias and Homogenizaton|
|MS-2.11-002|Conduct fairness assessments to measure systemic bias. Measure GAI system<br>performance across demographic groups and subgroups, addressing both<br>quality of service and any allocaton of services and resources. Quantfy harms<br>using: ﬁeld testng with sub-group populatons to determine likelihood of<br>exposure to generated content exhibitng harmful bias, AI red-teaming with<br>counterfactual and low-context (e.g., “leader,” “bad guys”) prompts. For ML<br>pipelines or business processes with categorical or numeric outcomes that rely<br>on GAI, apply general fairness metrics (e.g., demographic parity, equalized odds,<br>equal opportunity, statstcal hypothesis tests), to the pipeline or business<br>outcome where appropriate; Custom, context-speciﬁc metrics developed in<br>collaboraton with domain experts and aﬀected communites; Measurements of<br>the prevalence of denigraton in generated content in deployment (e.g., sub-<br>sampling a fracton of traﬃc and manually annotatng denigratng content).|Harmful Bias and Homogenizaton;<br>Dangerous, Violent, or Hateful<br>Content|
|MS-2.11-003|Identfy the classes of individuals, groups, or environmental ecosystems which<br>might be impacted by GAI systems through direct engagement with potentally<br>impacted communites.|Environmental; Harmful Bias and<br>Homogenizaton|
|MS-2.11-004|Review, document, and measure sources of bias in GAI training and TEVV data:<br>Diﬀerences in distributons of outcomes across and within groups, including<br>intersectng groups; Completeness, representatveness, and balance of data<br>sources; demographic group and subgroup coverage in GAI system training<br>data; Forms of latent systemic bias in images, text, audio, embeddings, or other<br>complex or unstructured data; Input data features that may serve as proxies for<br>demographic group membership (i.e., image metadata, language dialect) or<br>otherwise give rise to emergent bias within GAI systems; The extent to which<br>the digital divide may negatvely impact representatveness in GAI system<br>training and TEVV data; Filtering of hate speech or content in GAI system<br>training data; Prevalence of GAI-generated data in GAI system training data.|Harmful Bias and Homogenizaton|


15 Winogender Schemas is a sample set of paired sentences which differ only by gender of the pronouns used,
which can be used to evaluate gender bias in natural language processing coreference resolution systems.


36


|MS-2.11-005|Assess the proportion of synthetic to non-synthetci training data and verify<br>training data is not overly homogenous or GAI-produced to mitigate concerns of<br>model collapse.|Harmful Bias and Homogenization|
|---|---|---|
|**AI Actor Tasks: AI Deployment, AI Impact Assessment, Aﬀected Individuals and Communites, Domain Experts, End-Users,**<br>**Operaton and Monitoring, TEVV**|**AI Actor Tasks: AI Deployment, AI Impact Assessment, Aﬀected Individuals and Communites, Domain Experts, End-Users,**<br>**Operaton and Monitoring, TEVV**|**AI Actor Tasks: AI Deployment, AI Impact Assessment, Aﬀected Individuals and Communites, Domain Experts, End-Users,**<br>**Operaton and Monitoring, TEVV**|


|MEASURE 2.12: Environmental impact and sustainability of AI model training and management activities – as identified in the MAP<br>function – are assessed and documented.|Col2|Col3|
|---|---|---|
|**Acton ID**|**Suggested Acton**|**GAI Risks**|
|MS-2.12-001|Assess safety to physical environments when deploying GAI systems.|Dangerous, Violent, or Hateful<br>Content|
|MS-2.12-002|Document antcipated environmental impacts of model development,<br>maintenance, and deployment in product design decisions.|Environmental|
|MS-2.12-003|Measure or estmate environmental impacts (e.g., energy and water<br>consumpton) for training, ﬁne tuning, and deploying models: Verify tradeoﬀs<br>between resources used at inference tme versus additonal resources required<br>at training tme.|Environmental|
|MS-2.12-004|Verify eﬀectveness of carbon capture or oﬀset programs for GAI training and<br>applicatons, and address green-washing concerns.|Environmental|
|**AI Actor Tasks: AI Deployment, AI Impact Assessment, Domain Experts, Operaton and Monitoring, TEVV**|**AI Actor Tasks: AI Deployment, AI Impact Assessment, Domain Experts, Operaton and Monitoring, TEVV**|**AI Actor Tasks: AI Deployment, AI Impact Assessment, Domain Experts, Operaton and Monitoring, TEVV**|


37


|MEASURE 2.13: Effectiveness of the employed TEVV metrics and processes in the MEASURE function are evaluated and<br>documented.|Col2|Col3|
|---|---|---|
|**Acton ID**|**Suggested Acton**|**GAI Risks**|
|MS-2.13-001|Create measurement error models for pre-deployment metrics to demonstrate<br>construct validity for each metric (i.e., does the metric eﬀectvely operatonalize<br>the desired concept): Measure or estmate, and document, biases or statstcal<br>variance in applied metrics or structured human feedback processes; Leverage<br>domain expertse when modeling complex societal constructs such as hateful<br>content.|Confabulaton; Informaton<br>Integrity; Harmful Bias and<br>Homogenizaton|
|**AI Actor Tasks: AI Deployment, Operaton and Monitoring, TEVV**|**AI Actor Tasks: AI Deployment, Operaton and Monitoring, TEVV**|**AI Actor Tasks: AI Deployment, Operaton and Monitoring, TEVV**|


|MEASURE 3.2: Risk tracking approaches are considered for settings where AI risks are difficult to assess using currently available<br>measurement techniques or where metrics are not yet available.|Col2|Col3|
|---|---|---|
|**Acton ID**|**Suggested Acton**|**GAI Risks**|
|MS-3.2-001|Establish processes for identfying emergent GAI system risks including<br>consultng with external AI Actors.|Human-AI Conﬁguraton;<br>Confabulaton|
|**AI Actor Tasks: AI Impact Assessment, Domain Experts, Operaton and Monitoring, TEVV**|**AI Actor Tasks: AI Impact Assessment, Domain Experts, Operaton and Monitoring, TEVV**|**AI Actor Tasks: AI Impact Assessment, Domain Experts, Operaton and Monitoring, TEVV**|


|MEASURE 3.3: Feedback processes for end users and impacted communities to report problems and appeal system outcomes are<br>established and integrated into AI system evaluation metrics.|Col2|Col3|
|---|---|---|
|**Acton ID**|**Suggested Acton**|**GAI Risks**|
|MS-3.3-001|Conduct impact assessments on how AI-generated content might aﬀect<br>diﬀerent social, economic, and cultural groups.|Harmful Bias and Homogenizaton|
|MS-3.3-002|Conduct studies to understand how end users perceive and interact with GAI<br>content and accompanying content provenance within context of use. Assess<br>whether the content aligns with their expectatons and how they may act upon<br>the informaton presented.|Human-AI Conﬁguraton;<br>Informaton Integrity|
|MS-3.3-003|Evaluate potental biases and stereotypes that could emerge from the AI-<br>generated content using appropriate methodologies including computatonal<br>testng methods as well as evaluatng structured feedback input.|Harmful Bias and Homogenizaton|


38


|MS-3.3-004|Provide input for training materials about the capabilities and limitations of GAI<br>systems related to digital content transparency for AI Actors, other<br>professionals, and the public about the societal impacts of AI and the role of<br>diverse and inclusive content generation.|Human-AI Configuration;<br>Information Integrity; Harmful Bias<br>and Homogenization|
|---|---|---|
|MS-3.3-005|Record and integrate structured feedback about content provenance from<br>operators, users, and potentally impacted communites through the use of<br>methods such as user research studies, focus groups, or community forums.<br>Actvely seek feedback on generated content quality and potental biases.<br>Assess the general awareness among end users and impacted communites<br>about the availability of these feedback channels.|Human-AI Conﬁguraton;<br>Informaton Integrity; Harmful Bias<br>and Homogenizaton|
|**AI Actor Tasks: AI Deployment, Aﬀected Individuals and Communites, End-Users, Operaton and Monitoring, TEVV**|**AI Actor Tasks: AI Deployment, Aﬀected Individuals and Communites, End-Users, Operaton and Monitoring, TEVV**|**AI Actor Tasks: AI Deployment, Aﬀected Individuals and Communites, End-Users, Operaton and Monitoring, TEVV**|


|MEASURE 4.2: Measurement results regarding AI system trustworthiness in deployment context(s) and across the AI lifecycle are<br>informed by input from domain experts and relevant AI Actors to validate whether the system is performing consistently as<br>intended. Results are documented.|Col2|Col3|
|---|---|---|
|**Acton ID**|**Suggested Acton**|**GAI Risks**|
|MS-4.2-001|Conduct adversarial testng at a regular cadence to map and measure GAI risks,<br>including tests to address atempts to deceive or manipulate the applicaton of<br>provenance techniques or other misuses. Identfy vulnerabilites and<br>understand potental misuse scenarios and unintended outputs.|Informaton Integrity; Informaton<br>Security|
|MS-4.2-002|Evaluate GAI system performance in real-world scenarios to observe its<br>behavior in practcal environments and reveal issues that might not surface in<br>controlled and optmized testng environments.|Human-AI Conﬁguraton;<br>Confabulaton; Informaton<br>Security|
|MS-4.2-003|Implement interpretability and explainability methods to evaluate GAI system<br>decisions and verify alignment with intended purpose.|Informaton Integrity; Harmful Bias<br>and Homogenizaton|
|MS-4.2-004|Monitor and document instances where human operators or other systems<br>override the GAI's decisions. Evaluate these cases to understand if the overrides<br>are linked to issues related to content provenance.|Informaton Integrity|
|MS-4.2-005|Verify and document the incorporaton of results of structured public feedback<br>exercises into design, implementaton, deployment approval (“go”/“no-go”<br>decisions), monitoring, and decommission decisions.|Human-AI Conﬁguraton;<br>Informaton Security|
|**AI Actor Tasks: AI Deployment, Domain Experts, End-Users, Operaton and Monitoring, TEVV**<br>|**AI Actor Tasks: AI Deployment, Domain Experts, End-Users, Operaton and Monitoring, TEVV**<br>|**AI Actor Tasks: AI Deployment, Domain Experts, End-Users, Operaton and Monitoring, TEVV**<br>|


39


|MANAGE 1.3: Responses to the AI risks deemed high priority, as identified by the MAP function, are developed, planned, and<br>documented. Risk response options can include mitigating, transferring, avoiding, or accepting.|Col2|Col3|
|---|---|---|
|**Acton ID**|**Suggested Acton**|**GAI Risks**|
|MG-1.3-001|Document trade-oﬀs, decision processes, and relevant measurement and<br>feedback results for risks that do not surpass organizatonal risk tolerance, for<br>example, in the context of model release: Consider diﬀerent approaches for<br>model release, for example, leveraging a staged release approach. Consider<br>release approaches in the context of the model and its projected use cases.<br>Mitgate, transfer, or avoid risks that surpass organizatonal risk tolerances.|Informaton Security|
|MG-1.3-002|Monitor the robustness and eﬀectveness of risk controls and mitgaton plans<br>(e.g., via red-teaming, ﬁeld testng, partcipatory engagements, performance<br>assessments, user feedback mechanisms).|Human-AI Conﬁguraton|
|**AI Actor Tasks: AI Development, AI Deployment, AI Impact Assessment, Operaton and Monitoring** <br>|**AI Actor Tasks: AI Development, AI Deployment, AI Impact Assessment, Operaton and Monitoring** <br>|**AI Actor Tasks: AI Development, AI Deployment, AI Impact Assessment, Operaton and Monitoring** <br>|


|MANAGE 2.2: Mechanisms are in place and applied to sustain the value of deployed AI systems.|Col2|Col3|
|---|---|---|
|**Acton ID**|**Suggested Acton**|**GAI Risks**|
|MG-2.2-001|Compare GAI system outputs against pre-deﬁned organizaton risk tolerance,<br>guidelines, and principles, and review and test AI-generated content against<br>these guidelines.|CBRN Informaton or Capabilites;<br>Obscene, Degrading, and/or<br>Abusive Content; Harmful Bias and<br>Homogenizaton; Dangerous,<br>Violent, or Hateful Content|
|MG-2.2-002|Document training data sources to trace the origin and provenance of AI-<br>generated content.|Informaton Integrity|
|MG-2.2-003|Evaluate feedback loops between GAI system content provenance and human<br>reviewers, and update where needed. Implement real-tme monitoring systems<br>to aﬃrm that content provenance protocols remain eﬀectve.|Informaton Integrity|
|MG-2.2-004|Evaluate GAI content and data for representatonal biases and employ<br>techniques such as re-sampling, re-ranking, or adversarial training to mitgate<br>biases in the generated content.|Informaton Security; Harmful Bias<br>and Homogenizaton|
|MG-2.2-005|Engage in due diligence to analyze GAI output for harmful content, potental<br>misinformaton, and CBRN-related or NCII content.|CBRN Informaton or Capabilites;<br>Obscene, Degrading, and/or<br>Abusive Content; Harmful Bias and<br>Homogenizaton; Dangerous,<br>Violent, or Hateful Content|


40


|MG-2.2-006|Use feedback from internal and external AI Actors, users, individuals, and<br>communities, to assess impact of AI-generated content.|Human-AI Configuration|
|---|---|---|
|MG-2.2-007|Use real-tme auditng tools where they can be demonstrated to aid in the<br>tracking and validaton of the lineage and authentcity of AI-generated data.|Informaton Integrity|
|MG-2.2-008|Use structured feedback mechanisms to solicit and capture user input about AI-<br>generated content to detect subtle shifs in quality or alignment with<br>community and societal values.|Human-AI Conﬁguraton; Harmful<br>Bias and Homogenizaton|
|MG-2.2-009|Consider opportunites to responsibly use synthetc data and other privacy<br>enhancing techniques in GAI development, where appropriate and applicable,<br>match the statstcal propertes of real-world data without disclosing personally<br>identﬁable informaton or contributng to homogenizaton.|Data Privacy; Intellectual Property;<br>Informaton Integrity;<br>Confabulaton; Harmful Bias and<br>Homogenizaton|
|**AI Actor Tasks: AI Deployment, AI Impact Assessment, Governance and Oversight, Operaton and Monitoring**|**AI Actor Tasks: AI Deployment, AI Impact Assessment, Governance and Oversight, Operaton and Monitoring**|**AI Actor Tasks: AI Deployment, AI Impact Assessment, Governance and Oversight, Operaton and Monitoring**|


|MANAGE 2.3: Procedures are followed to respond to and recover from a previously unknown risk when it is identified.|Col2|Col3|
|---|---|---|
|**Acton ID**|**Suggested Acton**|**GAI Risks**|
|MG-2.3-001|Develop and update GAI system incident response and recovery plans and<br>procedures to address the following: Review and maintenance of policies and<br>procedures to account for newly encountered uses; Review and maintenance of<br>policies and procedures for detecton of unantcipated uses; Verify response<br>and recovery plans account for the GAI system value chain; Verify response and<br>recovery plans are updated for and include necessary details to communicate<br>with downstream GAI system Actors: Points-of-Contact (POC), Contact<br>informaton, notﬁcaton format.|Value Chain and Component<br>Integraton|
|**AI Actor Tasks: AI Deployment, Operaton and Monitoring**|**AI Actor Tasks: AI Deployment, Operaton and Monitoring**|**AI Actor Tasks: AI Deployment, Operaton and Monitoring**|


|MANAGE 2.4: Mechanisms are in place and applied, and responsibilities are assigned and understood, to supersede, disengage, or<br>deactivate AI systems that demonstrate performance or outcomes inconsistent with intended use.|Col2|Col3|
|---|---|---|
|**Acton ID**|**Suggested Acton**|**GAI Risks**|
|MG-2.4-001|Establish and maintain communicaton plans to inform AI stakeholders as part of<br>the deactvaton or disengagement process of a speciﬁc GAI system (including for<br>open-source models) or context of use, including reasons, workarounds, user<br>access removal, alternatve processes, contact informaton, etc.|Human-AI Conﬁguraton|


41


|MG-2.4-002|Establish and maintain procedures for escalating GAI system incidents to the<br>organizational risk management authority when specific criteria for deactivation<br>or disengagement is met for a particular context of use or for the GAI system as a<br>whole.|Information Security|
|---|---|---|
|MG-2.4-003|Establish and maintain procedures for the remediaton of issues which trigger<br>incident response processes for the use of a GAI system, and provide stakeholders<br>tmelines associated with the remediaton plan.|Informaton Security<br>|
|MG-2.4-004|Establish and regularly review speciﬁc criteria that warrants the deactvaton of<br>GAI systems in accordance with set risk tolerances and appettes.|Informaton Security<br>|
|**AI Actor Tasks: AI Deployment, Governance and Oversight, Operaton and Monitoring**|**AI Actor Tasks: AI Deployment, Governance and Oversight, Operaton and Monitoring**|**AI Actor Tasks: AI Deployment, Governance and Oversight, Operaton and Monitoring**|


|MANAGE 3.1: AI risks and benefits from third-party resources are regularly monitored, and risk controls are applied and<br>documented.|Col2|Col3|
|---|---|---|
|**Acton ID**|**Suggested Acton**|**GAI Risks**|
|MG-3.1-001|Apply organizatonal risk tolerances and controls (e.g., acquisiton and<br>procurement processes; assessing personnel credentals and qualiﬁcatons,<br>performing background checks; ﬁltering GAI input and outputs, grounding, ﬁne<br>tuning, retrieval-augmented generaton) to third-party GAI resources: Apply<br>organizatonal risk tolerance to the utlizaton of third-party datasets and other<br>GAI resources; Apply organizatonal risk tolerances to ﬁne-tuned third-party<br>models; Apply organizatonal risk tolerance to existng third-party models<br>adapted to a new domain; Reassess risk measurements afer ﬁne-tuning third-<br>party GAI models.|Value Chain and Component<br>Integraton; Intellectual Property|
|MG-3.1-002|Test GAI system value chain risks (e.g., data poisoning, malware, other sofware<br>and hardware vulnerabilites; labor practces; data privacy and localizaton<br>compliance; geopolitcal alignment).|Data Privacy; Informaton Security;<br>Value Chain and Component<br>Integraton; Harmful Bias and<br>Homogenizaton|
|MG-3.1-003|Re-assess model risks afer ﬁne-tuning or retrieval-augmented generaton<br>implementaton and for any third-party GAI models deployed for applicatons<br>and/or use cases that were not evaluated in inital testng.|Value Chain and Component<br>Integraton|
|MG-3.1-004|Take reasonable measures to review training data for CBRN informaton, and<br>intellectual property, and where appropriate, remove it. Implement reasonable<br>measures to prevent, ﬂag, or take other acton in response to outputs that<br>reproduce partcular training data (e.g., plagiarized, trademarked, patented,<br>licensed content or trade secret material).|Intellectual Property; CBRN<br>Informaton or Capabilites|


42


|MG-3.1-005|Review various transparency artifacts (e.g., system cards and model cards) for<br>third-party models.|Information Integrity; Information<br>Security; Value Chain and<br>Component Integration|
|---|---|---|
|**AI Actor Tasks: AI Deployment, Operaton and Monitoring, Third-party enttes**|**AI Actor Tasks: AI Deployment, Operaton and Monitoring, Third-party enttes**|**AI Actor Tasks: AI Deployment, Operaton and Monitoring, Third-party enttes**|


|MANAGE 3.2: Pre-trained models which are used for development are monitored as part of AI system regular monitoring and<br>maintenance.|Col2|Col3|
|---|---|---|
|**Acton ID**|**Suggested Acton**|**GAI Risks**|
|MG-3.2-001|Apply explainable AI (XAI) techniques (e.g., analysis of embeddings, model<br>compression/distllaton, gradient-based atributons, occlusion/term reducton,<br>counterfactual prompts, word clouds) as part of ongoing contnuous<br>improvement processes to mitgate risks related to unexplainable GAI systems.|Harmful Bias and Homogenizaton|
|MG-3.2-002|Document how pre-trained models have been adapted (e.g., ﬁne-tuned, or<br>retrieval-augmented generaton) for the speciﬁc generatve task, including any<br>data augmentatons, parameter adjustments, or other modiﬁcatons. Access to<br>un-tuned (baseline) models supports debugging the relatve inﬂuence of the pre-<br>trained weights compared to the ﬁne-tuned model weights or other system<br>updates.|Informaton Integrity; Data Privacy|
|MG-3.2-003|Document sources and types of training data and their origins, potental biases<br>present in the data related to the GAI applicaton and its content provenance,<br>architecture, training process of the pre-trained model including informaton on<br>hyperparameters, training duraton, and any ﬁne-tuning or retrieval-augmented<br>generaton processes applied.|Informaton Integrity; Harmful Bias<br>and Homogenizaton; Intellectual<br>Property|
|MG-3.2-004|Evaluate user reported problematc content and integrate feedback into system<br>updates.|Human-AI Conﬁguraton,<br>Dangerous, Violent, or Hateful<br>Content|
|MG-3.2-005|Implement content ﬁlters to prevent the generaton of inappropriate, harmful,<br>false, illegal, or violent content related to the GAI applicaton, including for CSAM<br>and NCII. These ﬁlters can be rule-based or leverage additonal machine learning<br>models to ﬂag problematc inputs and outputs.|Informaton Integrity; Harmful Bias<br>and Homogenizaton; Dangerous,<br>Violent, or Hateful Content;<br>Obscene, Degrading, and/or<br>Abusive Content|
|MG-3.2-006|Implement real-tme monitoring processes for analyzing generated content<br>performance and trustworthiness characteristcs related to content provenance<br>to identfy deviatons from the desired standards and trigger alerts for human<br>interventon.|Informaton Integrity|


43


|MG-3.2-007|Leverage feedback and recommendations from organizational boards or<br>commitet es related to the deployment of GAI applications and content<br>provenance when using third-party pre-trained models.|Information Integrity; Value Chain<br>and Component Integration|
|---|---|---|
|MG-3.2-008|Use human moderaton systems where appropriate to review generated content<br>in accordance with human-AI conﬁguraton policies established in the Govern<br>functon, aligned with socio-cultural norms in the context of use, and for setngs<br>where AI models are demonstrated to perform poorly.|Human-AI Conﬁguraton|
|MG-3.2-009|Use organizatonal risk tolerance to evaluate acceptable risks and performance<br>metrics and decommission or retrain pre-trained models that perform outside of<br>deﬁned limits.|CBRN Informaton or Capabilites;<br>Confabulaton|
|**AI Actor Tasks: AI Deployment, Operaton and Monitoring, Third-party enttes**|**AI Actor Tasks: AI Deployment, Operaton and Monitoring, Third-party enttes**|**AI Actor Tasks: AI Deployment, Operaton and Monitoring, Third-party enttes**|


|MANAGE 4.1: Post-deployment AI system monitoring plans are implemented, including mechanisms for capturing and evaluating<br>input from users and other relevant AI Actors, appeal and override, decommissioning, incident response, recovery, and change<br>management.|Col2|Col3|
|---|---|---|
|**Acton ID**|**Suggested Acton**|**GAI Risks**|
|MG-4.1-001|Collaborate with external researchers, industry experts, and community<br>representatves to maintain awareness of emerging best practces and<br>technologies in measuring and managing identﬁed risks.|Informaton Integrity; Harmful Bias<br>and Homogenizaton|
|MG-4.1-002|Establish, maintain, and evaluate eﬀectveness of organizatonal processes and<br>procedures for post-deployment monitoring of GAI systems, partcularly for<br>potental confabulaton, CBRN, or cyber risks.|CBRN Informaton or Capabilites;<br>Confabulaton; Informaton<br>Security|
|MG-4.1-003|Evaluate the use of sentment analysis to gauge user sentment regarding GAI<br>content performance and impact, and work in collaboraton with AI Actors<br>experienced in user research and experience.|Human-AI Conﬁguraton|
|MG-4.1-004|Implement actve learning techniques to identfy instances where the model fails<br>or produces unexpected outputs.|Confabulaton|
|MG-4.1-005|Share transparency reports with internal and external stakeholders that detail<br>steps taken to update the GAI system to enhance transparency and<br>accountability.|Human-AI Conﬁguraton; Harmful<br>Bias and Homogenizaton|
|MG-4.1-006|Track dataset modiﬁcatons for provenance by monitoring data deletons,<br>rectﬁcaton requests, and other changes that may impact the veriﬁability of<br>content origins.|Informaton Integrity|


44


|MG-4.1-007|Verify that AI Actors responsible for monitoring reported issues can effectively<br>evaluate GAI system performance including the application of content<br>provenance data tracking techniques, and promptly escalate issues for response.|Human-AI Configuration;<br>Information Integrity|
|---|---|---|
|**AI Actor Tasks: AI Deployment, Aﬀected Individuals and Communites, Domain Experts, End-Users, Human Factors, Operaton and**<br>**Monitoring**|**AI Actor Tasks: AI Deployment, Aﬀected Individuals and Communites, Domain Experts, End-Users, Human Factors, Operaton and**<br>**Monitoring**|**AI Actor Tasks: AI Deployment, Aﬀected Individuals and Communites, Domain Experts, End-Users, Human Factors, Operaton and**<br>**Monitoring**|


|MANAGE 4.2: Measurable activities for continual improvements are integrated into AI system updates and include regular<br>engagement with interested parties, including relevant AI Actors.|Col2|Col3|
|---|---|---|
|**Acton ID**|**Suggested Acton**|**GAI Risks**|
|MG-4.2-001|Conduct regular monitoring of GAI systems and publish reports detailing the<br>performance, feedback received, and improvements made.|Harmful Bias and Homogenizaton|
|MG-4.2-002|Practce and follow incident response plans for addressing the generaton of<br>inappropriate or harmful content and adapt processes based on ﬁndings to<br>prevent future occurrences. Conduct post-mortem analyses of incidents with<br>relevant AI Actors, to understand the root causes and implement preventve<br>measures.|Human-AI Conﬁguraton;<br>Dangerous, Violent, or Hateful<br>Content|
|MG-4.2-003|Use visualizatons or other methods to represent GAI model behavior to ease<br>non-technical stakeholders understanding of GAI system functonality.|Human-AI Conﬁguraton|
|**AI Actor Tasks: AI Deployment, AI Design, AI Development, Aﬀected Individuals and Communites, End-Users, Operaton and**<br>**Monitoring, TEVV**|**AI Actor Tasks: AI Deployment, AI Design, AI Development, Aﬀected Individuals and Communites, End-Users, Operaton and**<br>**Monitoring, TEVV**|**AI Actor Tasks: AI Deployment, AI Design, AI Development, Aﬀected Individuals and Communites, End-Users, Operaton and**<br>**Monitoring, TEVV**|


|MANAGE 4.3: Incidents and errors are communicated to relevant AI Actors, including affected communities. Processes for tracking,<br>responding to, and recovering from incidents and errors are followed and documented.|Col2|Col3|
|---|---|---|
|**Acton ID**|**Suggested Acton**|**GAI Risks**|
|MG-4.3-001|Conduct afer-acton assessments for GAI system incidents to verify incident<br>response and recovery processes are followed and eﬀectve, including to follow<br>procedures for communicatng incidents to relevant AI Actors and where<br>applicable, relevant legal and regulatory bodies.|Informaton Security|
|MG-4.3-002|Establish and maintain policies and procedures to record and track GAI system<br>reported errors, near-misses, and negatve impacts.|Confabulaton; Informaton<br>Integrity|


45


|MG-4.3-003|Report GAI incidents in compliance with legal and regulatory requirements (e.g.,<br>HIPAA breach reporting, e.g., OCR (2023) or NHTSA (2022) autonomous vehicle<br>crash reporting requirements.|Information Security; Data Privacy|
|---|---|---|
|**AI Actor Tasks: AI Deployment, Aﬀected Individuals and Communites, Domain Experts, End-Users, Human Factors, Operaton and**<br>**Monitoring** <br>|**AI Actor Tasks: AI Deployment, Aﬀected Individuals and Communites, Domain Experts, End-Users, Human Factors, Operaton and**<br>**Monitoring** <br>|**AI Actor Tasks: AI Deployment, Aﬀected Individuals and Communites, Domain Experts, End-Users, Human Factors, Operaton and**<br>**Monitoring** <br>|


46


**Appendix A.** **Primary GAI Considerations**


The following primary considerations were derived as overarching themes from the GAI PWG
consultation process. These considerations (Governance, Pre-Deployment Testing, Content Provenance,
and Incident Disclosure) are relevant for voluntary use by any organization designing, developing, and
using GAI and also inform the Actions to Manage GAI risks. Information included about the primary
considerations is not exhaustive, but highlights the most relevant topics derived from the GAI PWG.

Acknowledgments: These considerations could not have been surfaced without the helpful analysis and
contributions from the community and NIST staff GAI PWG leads: George Awad, Luca Belli, Harold Booth,
Mat Heyman, Yooyoung Lee, Mark Pryzbocki, Reva Schwartz, Martin Stanley, and Kyra Yee.


**A.1.** **Governance**


**A.1.1.** **Overview**


Like any other technology system, governance principles and techniques can be used to manage risks
related to generative AI models, capabilities, and applications. Organizations may choose to apply their
existing risk tiering to GAI systems, or they may opt to revise or update AI system risk levels to address
these unique GAI risks. This section describes how organizational governance regimes may be reevaluated and adjusted for GAI contexts. It also addresses third-party considerations for governing across
the AI value chain.


**A.1.2.** **Organizational Governance**


GAI opportunities, risks and long-term performance characteristics are typically less well-understood
than non-generative AI tools and may be perceived and acted upon by humans in ways that vary greatly.
Accordingly, GAI may call for different levels of oversight from AI Actors or different human-AI
configurations in order to manage their risks effectively. Organizations’ use of GAI systems may also
warrant additional human review, tracking and documentation, and greater management oversight.

AI technology can produce varied outputs in multiple modalities and present many classes of user
interfaces. This leads to a broader set of AI Actors interacting with GAI systems for widely differing
applications and contexts of use. These can include data labeling and preparation, development of GAI
models, content moderation, code generation and review, text generation and editing, image and video
generation, summarization, search, and chat. These activities can take place within organizational
settings or in the public domain.

Organizations can restrict AI applications that cause harm, exceed stated risk tolerances, or that conflict
with their tolerances or values. Governance tools and protocols that are applied to other types of AI
systems can be applied to GAI systems. These plans and actions include:


- Accessibility and reasonable
accommodations

- AI actor credentials and qualifications

- Alignment to organizational values


- Auditing and assessment

- Change-management controls

- Commercial use

- Data provenance


47


- Data protection

- Data retention

- Consistency in use of defining key terms

- Decommissioning

- Discouraging anonymous use

- Education

- Impact assessments

- Incident response

- Monitoring

- Opt-outs


- Risk-based controls

- Risk mapping and measurement

- Science-backed TEVV practices

- Secure software development practices

- Stakeholder engagement

- Synthetic content detection and
labeling tools and techniques

- Whistleblower protections

- Workforce diversity and
interdisciplinary teams


Establishing acceptable use policies and guidance for the use of GAI in formal human-AI teaming settings
as well as different levels of human-AI configurations can help to decrease risks arising from misuse,
abuse, inappropriate repurpose, and misalignment between systems and users. These practices are just
one example of adapting existing governance protocols for GAI contexts.


**A.1.3.** **Third-Party Considerations**


Organizations may seek to acquire, embed, incorporate, or use open-source or proprietary third-party
GAI models, systems, or generated data for various applications across an enterprise. Use of these GAI
tools and inputs has implications for all functions of the organization – including but not limited to
acquisition, human resources, legal, compliance, and IT services – regardless of whether they are carried
out by employees or third parties. Many of the actions cited above are relevant and options for
addressing third-party considerations.

Third party GAI integrations may give rise to increased intellectual property, data privacy, or information
security risks, pointing to the need for clear guidelines for transparency and risk management regarding
the collection and use of third-party data for model inputs. Organizations may consider varying risk
controls for foundation models, fine-tuned models, and embedded tools, enhanced processes for
interacting with external GAI technologies or service providers. Organizations can apply standard or
existing risk controls and processes to proprietary or open-source GAI technologies, data, and third-party
service providers, including acquisition and procurement due diligence, requests for software bills of
materials (SBOMs), application of service level agreements (SLAs), and statement on standards for
attestation engagement (SSAE) reports to help with third-party transparency and risk management for
GAI systems.


**A.1.4.** **Pre-Deployment Testing**


**Overview**

The diverse ways and contexts in which GAI systems may be developed, used, and repurposed
complicates risk mapping and pre-deployment measurement efforts. Robust test, evaluation, validation,
and verification (TEVV) processes can be iteratively applied – and documented – in early stages of the AI
[lifecycle and informed by representative AI Actors (see Figure 3 of the AI RMF). Until new and rigorous](https://nvlpubs.nist.gov/nistpubs/ai/nist.ai.100-1.pdf)


48


early lifecycle TEVV approaches are developed and matured for GAI, organizations may use
recommended “pre-deployment testing” practices to measure performance, capabilities, limits, risks,
and impacts. This section describes risk measurement and estimation as part of pre-deployment TEVV,
and examines the state of play for pre-deployment testing methodologies.

**Limitations of Current Pre-deployment Test Approaches**

Currently available pre-deployment TEVV processes used for GAI applications may be inadequate, nonsystematically applied, or fail to reflect or mismatched to deployment contexts. For example, the
anecdotal testing of GAI system capabilities through video games or standardized tests designed for
humans (e.g., intelligence tests, professional licensing exams) does not guarantee GAI system validity or
reliability in those domains. Similarly, jailbreaking or prompt engineering tests may not systematically
assess validity or reliability risks.

Measurement gaps can arise from mismatches between laboratory and real-world settings. Current
testing approaches often remain focused on laboratory conditions or restricted to benchmark test
datasets and in silico techniques that may not extrapolate well to—or directly assess GAI impacts in realworld conditions. For example, current measurement gaps for GAI make it difficult to precisely estimate
its potential ecosystem-level or longitudinal risks and related political, social, and economic impacts.
Gaps between benchmarks and real-world use of GAI systems may likely be exacerbated due to prompt
sensitivity and broad heterogeneity of contexts of use.


**A.1.5.** **Structured Public Feedback**


Structured public feedback can be used to evaluate whether GAI systems are performing as intended
and to calibrate and verify traditional measurement methods. Examples of structured feedback include,
but are not limited to:

  - **Participatory Engagement Methods** : Methods used to solicit feedback from civil society groups,
affected communities, and users, including focus groups, small user studies, and surveys.

  - **Field Testing** : Methods used to determine how people interact with, consume, use, and make
sense of AI-generated information, and subsequent actions and effects, including UX, usability,
and other structured, randomized experiments.

  - **AI Red-teaming:** A [structured testng exercise](https://www.whitehouse.gov/briefing-room/presidential-actions/2023/10/30/executive-order-on-the-safe-secure-and-trustworthy-development-and-use-of-artificial-intelligence/) used to probe an AI system to find flaws and
vulnerabilities such as inaccurate, harmful, or discriminatory outputs, often in a controlled
environment and in collaboration with system developers.

Information gathered from structured public feedback can inform design, implementation, deployment
approval, maintenance, or decommissioning decisions. Results and insights gleaned from these exercises
can serve multiple purposes, including improving data quality and preprocessing, bolstering governance
decision making, and enhancing system documentation and debugging practices. When implementing
feedback activities, organizations should follow human subjects research requirements and best
practices such as informed consent and subject compensation.


49


**Participatory Engagement Methods**

On an ad hoc or more structured basis, organizations can design and use a variety of channels to engage
external stakeholders in product development or review. Focus groups with select experts can provide
feedback on a range of issues. Small user studies can provide feedback from representative groups or
populations. Anonymous surveys can be used to poll or gauge reactions to specific features. Participatory
engagement methods are often less structured than field testing or red teaming, and are more
commonly used in early stages of AI or product development.

**Field Testing**

Field testing involves structured settings to evaluate risks and impacts and to simulate the conditions
under which the GAI system will be deployed. Field style tests can be adapted from a focus on user
preferences and experiences towards AI risks and impacts – both negative and positive. When carried
out with large groups of users, these tests can provide estimations of the likelihood of risks and impacts
in real world interactions.

Organizations may also collect feedback on outcomes, harms, and user experience directly from users in
the production environment after a model has been released, in accordance with human subject
standards such as informed consent and compensation. Organizations should follow applicable human
subjects research requirements, and best practices such as informed consent and subject compensation,
when implementing feedback activities.

**AI Red-teaming**

AI red-teaming is an evolving practice that references exercises often conducted in a controlled
environment and in collaboration with AI developers building AI models to identify potential adverse
behavior or outcomes of a GAI model or system, how they could occur, and stress test safeguards”. AI
red-teaming can be performed before or after AI models or systems are made available to the broader
public; this section focuses on red-teaming in pre-deployment contexts.

The quality of AI red-teaming outputs is related to the background and expertise of the AI red team
itself. Demographically and interdisciplinarily diverse AI red teams can be used to identify flaws in the
varying contexts where GAI will be used. For best results, AI red teams should demonstrate domain
expertise, and awareness of socio-cultural aspects within the deployment context. AI red-teaming results
should be given additional analysis before they are incorporated into organizational governance and
decision making, policy and procedural updates, and AI risk management efforts.

Various types of AI red-teaming may be appropriate, depending on the use case:

  - General Public: Performed by general users (not necessarily AI or technical experts) who are
expected to use the model or interact with its outputs, and who bring their own lived
experiences and perspectives to the task of AI red-teaming. These individuals may have been
provided instructions and material to complete tasks which may elicit harmful model behaviors.
This type of exercise can be more effective with large groups of AI red-teamers.

  - Expert: Performed by specialists with expertise in the domain or specific AI red-teaming context
of use (e.g., medicine, biotech, cybersecurity).

  - Combination: In scenarios when it is difficult to identify and recruit specialists with sufficient
domain and contextual expertise, AI red-teaming exercises may leverage both expert and


50


general public participants. For example, expert AI red-teamers could modify or verify the
prompts written by general public AI red-teamers. These approaches may also expand coverage
of the AI risk attack surface.

  - Human / AI: Performed by GAI in [combinaton with specialist or non-specialist human teams.](https://arxiv.org/pdf/2401.15897)
GAI-led red-teaming can be more cost effective than human red-teamers alone. Human or GAIled AI red-teaming may be better suited for eliciting different types of harms.


**A.1.6.** **Content Provenance**


**Overview**

GAI technologies can be leveraged for many applications such as content generation and synthetic data.
Some aspects of GAI outputs, such as the production of deepfake content, can challenge our ability to
distinguish human-generated content from AI-generated synthetic content. To help manage and mitigate
these risks, digital transparency mechanisms like provenance data tracking can trace the origin and
history of content. Provenance data tracking and synthetic content detection can help facilitate greater
information access about both authentic and synthetic content to users, enabling better knowledge of
trustworthiness in AI systems. When combined with other organizational accountability mechanisms,
digital content transparency approaches can enable processes to trace negative outcomes back to their
source, improve information integrity, and uphold public trust. Provenance data tracking and synthetic
content detection mechanisms provide information about the [origin and history of content to assist in](https://www.itic.org/policy/ITI_AIContentAuthorizationPolicy_122123.pdf)
GAI risk management efforts.

Provenance metadata can include information about GAI model developers or creators of GAI content,
date/time of creation, location, modifications, and sources. Metadata can be tracked for text, images,
videos, audio, and underlying datasets. The implementation of provenance data tracking techniques can
help assess the authenticity, integrity, intellectual property rights, and potential manipulations in digital
content. Some well-known techniques for provenance data tracking [include digital](https://www.semanticscholar.org/paper/Provable-Robust-Watermarking-for-AI-Generated-%20Text-Zhao-Ananth/e3ee09fb2bcc29e992cdcf0d0db6fcb6e5c56384) [watermarking,](https://openreview.net/forum?id=aX8ig9X2a7)
metadata recording, digital fingerprinting, and human authentication, [among others.](https://partnershiponai.org/glossary-for-synthetic-media-transparency-methods-part-1-indirect-disclosure/)

**Provenance Data Tracking Approaches**

Provenance data tracking techniques for GAI systems can be used to track the history and origin of data
inputs, metadata, and synthetic content. Provenance data tracking records the origin and history for
digital content, allowing its authenticity to be determined. It consists of techniques to record metadata
as well as overt and covert digital watermarks on content. Data provenance refers to tracking the origin
and history of input data through metadata and digital watermarking techniques. Provenance data
tracking processes can include and assist AI Actors across the lifecycle who may not have full visibility or
control over the various trade-offs and cascading impacts of early-stage model decisions on downstream
performance and synthetic outputs. For example, by selecting a watermarking model to prioritize
[robustness (the durability of a watermark), an AI actor may inadvertently diminish computatonal](https://ieeexplore.ieee.org/stamp/stamp.jsp?arnumber=7057071&tag=1)
[complexity](https://ieeexplore.ieee.org/stamp/stamp.jsp?arnumber=7057071&tag=1) (the resources required to implement watermarking). Organizational risk management
efforts for enhancing content provenance include:

  - Tracking provenance of training data and metadata for GAI systems;

  - Documenting provenance data limitations within GAI systems;


51


  - Monitoring system capabilities and limitations in deployment through rigorous TEVV processes;

  - Evaluating how humans engage, interact with, or adapt to GAI content (especially in decision
making tasks informed by GAI content), and how they react to applied provenance techniques
such as overt disclosures.

Organizations can document and delineate GAI system objectives and limitations to identify gaps where
provenance data may be most useful. For instance, GAI systems used for content creation may require
robust watermarking techniques and corresponding detectors to identify the source of content or
metadata recording techniques and metadata management tools and repositories to trace content
origins and modifications. Further narrowing of GAI task definitions to include provenance data can
enable organizations to maximize the utility of provenance data and risk management efforts.


**A.1.7.** **Enhancing Content Provenance through Structured Public Feedback**


While indirect feedback methods such as automated error collection systems are useful, they often lack
the [context and depth](https://arxiv.org/abs/2304.02819) that direct input from end users can provide. Organizations can leverage feedback
approaches described in the Pre-Deployment Testng secton to capture input from external sources such
as through AI red-teaming.

Integrating pre- and post-deployment external feedback into the monitoring process for GAI models and
corresponding applications can help enhance awareness of performance changes and mitigate potential
risks and harms from outputs. There are many ways to capture and make use of user feedback – before
and after GAI systems and digital content transparency approaches are deployed – to gain insights about
authentication efficacy and vulnerabilities, impacts of adversarial threats on techniques, and unintended
consequences resulting from the utilization of content provenance approaches on users and
communities. Furthermore, organizations can track and document the provenance of datasets to identify
instances in which AI-generated data is a potential root cause of performance issues with the GAI
system.


**A.1.8.** **Incident Disclosure**


**Overview**

AI incidents can be [defned](https://oecd.ai/en/incidents-methodology) as an “event, circumstance, or series of events where the development, use,
or malfunction of one or more AI systems directly or indirectly contributes to one of the following harms:
injury or harm to the health of a person or groups of people (including psychological harms and harms to
mental health); disruption of the management and operation of critical infrastructure; violations of
human rights or a breach of obligations under applicable law intended to protect fundamental, labor,
and intellectual property rights; or harm to property, communities, or the environment.” AI incidents can
occur in the aggregate (i.e., for systemic discrimination) or acutely (i.e., for one individual).

**State of AI Incident Tracking and Disclosure**

Formal channels do not currently exist to report and document AI incidents. However, a number of
[publicly available databases](https://incidentdatabase.ai/) have been created to document their occurrence. These reporting channels
make decisions on an ad hoc basis about what kinds of incidents to track. Some, for example, track by
[amount of media coverage.](https://oecd.ai/en/incidents-methodology)


52


Documenting, reporting, and sharing information about GAI incidents can help mitigate and prevent
harmful outcomes by assisting relevant AI Actors in [tracing impacts to their source. Greater awareness](https://dl.acm.org/doi/fullHtml/10.1145/3600211.3604700)
and standardization of GAI incident reporting could promote this transparency and improve GAI risk
management across the AI ecosystem.

**Documentation and Involvement of AI Actors**

AI Actors should be aware of their roles in reporting AI incidents. To better understand previous incidents
and implement measures to prevent similar ones in the future, organizations could consider developing
guidelines for publicly available incident reporting which include information about AI actor
responsibilities. These guidelines would help AI system operators identify GAI incidents across the AI
lifecycle and with AI Actors regardless of role. Documentation and review of third-party inputs and
plugins for GAI systems is especially important for AI Actors in the context of incident disclosure; LLM
inputs and content delivered through these [plugins is ofen distributed,](https://owasp.org/www-project-top-10-for-large-language-model-applications/) with inconsistent or insufficient
access control.

Documentation practices including logging, recording, and analyzing GAI incidents can facilitate
smoother sharing of information with relevant AI Actors. Regular information sharing, change
management records, version history and metadata can also empower AI Actors responding to and
managing AI incidents.


53


**Appendix B.** **References**


Acemoglu, D. (2024) The Simple Macroeconomics of AI [htps://www.nber.org/papers/w32487](https://www.nber.org/papers/w32487)

[AI Incident Database. htps://incidentdatabase.ai/](https://incidentdatabase.ai/)

Atherton, D. (2024) Deepfakes and Child Safety: A Survey and Analysis of 2023 Incidents and Responses.
_AI Incident Database._ [htps://incidentdatabase.ai/blog/deepfakes-and-child-safety/](https://incidentdatabase.ai/blog/deepfakes-and-child-safety/)

Badyal, N. et al. (2023) Intentional Biases in LLM Responses. _arXiv_ . [htps://arxiv.org/pdf/2311.07611](https://arxiv.org/pdf/2311.07611)

Bing Chat: Data Exfiltration Exploit Explained. _Embrace The Red_ .
[htps://embracethered.com/blog/posts/2023/bing-chat-data-exfltraton-poc-and-fx/](https://embracethered.com/blog/posts/2023/bing-chat-data-exfiltration-poc-and-fix/)

Bommasani, R. et al. (2022) Picking on the Same Person: Does Algorithmic Monoculture lead to Outcome
Homogenization? _arXiv_ . [htps://arxiv.org/pdf/2211.13972](https://arxiv.org/pdf/2211.13972)

Boyarskaya, M. et al. (2020) Overcoming Failures of Imagination in AI Infused System Development and
Deployment. _arXiv_ . [htps://arxiv.org/pdf/2011.13416](https://arxiv.org/pdf/2011.13416)

Browne, D. et al. (2023) Securing the AI Pipeline. _Mandiant_ .
[htps://www.mandiant.com/resources/blog/securing-ai-pipeline](https://www.mandiant.com/resources/blog/securing-ai-pipeline)

Burgess, M. (2024) Generative AI’s Biggest Security Flaw Is Not Easy to Fix. _WIRED_ .
[htps://www.wired.com/story/generatve-ai-prompt-injecton-hacking/](https://www.wired.com/story/generative-ai-prompt-injection-hacking/)

Burtell, M. et al. (2024) The Surprising Power of Next Word Prediction: Large Language Models
Explained, Part 1. _Georgetown Center for Security and Emerging Technology_ .
[htps://cset.georgetown.edu/artcle/the-surprising-power-of-next-word-predicton-large-language-](https://cset.georgetown.edu/article/the-surprising-power-of-next-word-prediction-large-language-models-explained-part-1/)
[models-explained-part-1/](https://cset.georgetown.edu/article/the-surprising-power-of-next-word-prediction-large-language-models-explained-part-1/)

Canadian Centre for Cyber Security (2023) Generative artificial intelligence (AI) - ITSAP.00.041.
[htps://www.cyber.gc.ca/en/guidance/generatve-artfcial-intelligence-ai-itsap00041](https://www.cyber.gc.ca/en/guidance/generative-artificial-intelligence-ai-itsap00041)

Carlini, N., et al. (2021) Extracting Training Data from Large Language Models. _Usenix_ .
[htps://www.usenix.org/conference/usenixsecurity21/presentaton/carlini-extractng](https://www.usenix.org/conference/usenixsecurity21/presentation/carlini-extracting)

Carlini, N. et al. (2023) Quantifying Memorization Across Neural Language Models. _ICLR 2023_ .
[htps://arxiv.org/pdf/2202.07646](https://arxiv.org/pdf/2202.07646)

Carlini, N. et al. (2024) Stealing Part of a Production Language Model. _arXiv_ .
[htps://arxiv.org/abs/2403.06634](https://arxiv.org/abs/2403.06634)

Chandra, B. et al. (2023) Dismantling the Disinformation Business of Chinese Influence Operations.
_RAND_ . [htps://www.rand.org/pubs/commentary/2023/10/dismantling-the-disinformaton-business-of-](https://www.rand.org/pubs/commentary/2023/10/dismantling-the-disinformation-business-of-chinese.html)
[chinese.html](https://www.rand.org/pubs/commentary/2023/10/dismantling-the-disinformation-business-of-chinese.html)

Ciriello, R. et al. (2024) Ethical Tensions in Human-AI Companionship: A Dialectical Inquiry into Replika.
_ResearchGate._ [htps://www.researchgate.net/publicaton/374505266_Ethical_Tensions_in_Human-](https://www.researchgate.net/publication/374505266_Ethical_Tensions_in_Human-AI_Companionship_A_Dialectical_Inquiry_into_Replika)
[AI_Companionship_A_Dialectcal_Inquiry_into_Replika](https://www.researchgate.net/publication/374505266_Ethical_Tensions_in_Human-AI_Companionship_A_Dialectical_Inquiry_into_Replika)

Dahl, M. et al. (2024) Large Legal Fictions: Profiling Legal Hallucinations in Large Language Models. _arXiv_ .
[htps://arxiv.org/abs/2401.01301](https://arxiv.org/abs/2401.01301)


54


De Angelo, D. (2024) Short, Mid and Long-Term Impacts of AI in Cybersecurity. _Palo Alto Networks_ .
[htps://www.paloaltonetworks.com/blog/2024/02/impacts-of-ai-in-cybersecurity/](https://www.paloaltonetworks.com/blog/2024/02/impacts-of-ai-in-cybersecurity/)

De Freitas, J. et al. (2023) Chatbots and Mental Health: Insights into the Safety of Generative AI. _Harvard_
_Business School_ [. htps://www.hbs.edu/ris/Publicaton%20Files/23-011_c1bdd417-f717-47b6-bccb-](https://www.hbs.edu/ris/Publication%20Files/23-011_c1bdd417-f717-47b6-bccb-5438c6e65c1a_f6fd9798-3c2d-4932-b222-056231fe69d7.pdf)
[5438c6e65c1a_f6fd9798-3c2d-4932-b222-056231fe69d7.pdf](https://www.hbs.edu/ris/Publication%20Files/23-011_c1bdd417-f717-47b6-bccb-5438c6e65c1a_f6fd9798-3c2d-4932-b222-056231fe69d7.pdf)

Dietvorst, B. et al. (2014) Algorithm Aversion: People Erroneously Avoid Algorithms After Seeing Them
Err. _Journal of Experimental Psychology_ . [htps://marketng.wharton.upenn.edu/wp-](https://marketing.wharton.upenn.edu/wp-content/uploads/2016/10/Dietvorst-Simmons-Massey-2014.pdf)
[content/uploads/2016/10/Dietvorst-Simmons-Massey-2014.pdf](https://marketing.wharton.upenn.edu/wp-content/uploads/2016/10/Dietvorst-Simmons-Massey-2014.pdf)

Duhigg, C. (2012) How Companies Learn Your Secrets. _New York Times_ .
[htps://www.nytmes.com/2012/02/19/magazine/shopping-habits.html](https://www.nytimes.com/2012/02/19/magazine/shopping-habits.html)

Elsayed, G. et al. (2024) Images altered to trick machine vision can influence humans too. _Google_
_DeepMind_ [. htps://deepmind.google/discover/blog/images-altered-to-trick-machine-vision-can-](https://deepmind.google/discover/blog/images-altered-to-trick-machine-vision-can-influence-humans-too/)
[infuence-humans-too/](https://deepmind.google/discover/blog/images-altered-to-trick-machine-vision-can-influence-humans-too/)

Epstein, Z. et al. (2023). Art and the science of generative AI. _Science_ .
[htps://www.science.org/doi/10.1126/science.adh4451](https://www.science.org/doi/10.1126/science.adh4451)

Feffer, M. et al. (2024) Red-Teaming for Generative AI: Silver Bullet or Security Theater? _arXiv._
[htps://arxiv.org/pdf/2401.15897](https://arxiv.org/pdf/2401.15897)

Glazunov, S. et al. (2024) Project Naptime: Evaluating Offensive Security Capabilities of Large Language
Models. _Project Zero._ [htps://googleprojectzero.blogspot.com/2024/06/project-naptme.html](https://googleprojectzero.blogspot.com/2024/06/project-naptime.html)

Greshake, K. et al. (2023) Not what you've signed up for: Compromising Real-World LLM-Integrated
Applications with Indirect Prompt Injection. _arXiv_ . [htps://arxiv.org/abs/2302.12173](https://arxiv.org/abs/2302.12173)

Hagan, M. (2024) Good AI Legal Help, Bad AI Legal Help: Establishing quality standards for responses to
people’s legal problem stories. _SSRN._ [htps://papers.ssrn.com/sol3/papers.cfm?abstract_id=4696936](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4696936)

Haran, R. (2023) Securing LLM Systems Against Prompt Injection. _NVIDIA_ .
[htps://developer.nvidia.com/blog/securing-llm-systems-against-prompt-injecton/](https://developer.nvidia.com/blog/securing-llm-systems-against-prompt-injection/)

Information Technology Industry Council (2024) Authenticating AI-Generated Content.
[htps://www.itc.org/policy/ITI_AIContentAuthorizatonPolicy_122123.pdf](https://www.itic.org/policy/ITI_AIContentAuthorizationPolicy_122123.pdf)

Jain, S. et al. (2023) Algorithmic Pluralism: A Structural Approach To Equal Opportunity. _arXiv_ .
[htps://arxiv.org/pdf/2305.08157](https://arxiv.org/pdf/2305.08157)

Ji, Z. et al (2023) Survey of Hallucination in Natural Language Generation. ACM Comput. Surv. 55, 12,
Article 248. [htps://doi.org/10.1145/3571730](https://doi.org/10.1145/3571730)

Jones-Jang, S. et al. (2022) How do people react to AI failure? Automation bias, algorithmic aversion, and
perceived controllability. _Oxford._ [htps://academic.oup.com/jcmc/artcle/28/1/zmac029/6827859]](https://academic.oup.com/jcmc/article/28/1/zmac029/6827859)

Jussupow, E. et al. (2020) Why Are We Averse Towards Algorithms? A Comprehensive Literature Review
on Algorithm Aversion. _ECIS 2020_ . [htps://aisel.aisnet.org/ecis2020_rp/168/](https://aisel.aisnet.org/ecis2020_rp/168/)

Kalai, A., et al. (2024) Calibrated Language Models Must Hallucinate. _arXiv._
[htps://arxiv.org/pdf/2311.14648](https://arxiv.org/pdf/2311.14648)


55


Karasavva, V. et al. (2021) Personality, Atiudinal, and Demographic Predictors of Non-consensual
Dissemination of Intimate Images. _NIH._ [htps://www.ncbi.nlm.nih.gov/pmc/artcles/PMC9554400/](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC9554400/)

Katzman, J., et al. (2023) Taxonomizing and measuring representational harms: a look at image tagging.
_AAAI_ . [htps://dl.acm.org/doi/10.1609/aaai.v37i12.26670](https://dl.acm.org/doi/10.1609/aaai.v37i12.26670)

Khan, T. et al. (2024) From Code to Consumer: PAI’s Value Chain Analysis Illuminates Generative AI’s Key
Players. _AI._ [htps://partnershiponai.org/from-code-to-consumer-pais-value-chain-analysis-illuminates-](https://partnershiponai.org/from-code-to-consumer-pais-value-chain-analysis-illuminates-generative-ais-key-players/)
[generatve-ais-key-players/](https://partnershiponai.org/from-code-to-consumer-pais-value-chain-analysis-illuminates-generative-ais-key-players/)

Kirchenbauer, J. et al. (2023) A Watermark for Large Language Models. _OpenReview_ .
[htps://openreview.net/forum?id=aX8ig9X2a7](https://openreview.net/forum?id=aX8ig9X2a7)

Kleinberg, J. et al. (May 2021) Algorithmic monoculture and social welfare. _PNAS_ .
[htps://www.pnas.org/doi/10.1073/pnas.2018340118](https://www.pnas.org/doi/10.1073/pnas.2018340118)

Lakatos, S. (2023) A Revealing Picture. _Graphika_ . [htps://graphika.com/reports/a-revealing-picture](https://graphika.com/reports/a-revealing-picture)

Lee, H. et al. (2024) Deepfakes, Phrenology, Surveillance, and More! A Taxonomy of AI Privacy Risks.
_arXiv._ [htps://arxiv.org/pdf/2310.07879](https://arxiv.org/pdf/2310.07879)

Lenaerts-Bergmans, B. (2024) Data Poisoning: The Exploitation of Generative AI. _Crowdstrike_ .
[htps://www.crowdstrike.com/cybersecurity-101/cyberatacks/data-poisoning/](https://www.crowdstrike.com/cybersecurity-101/cyberattacks/data-poisoning/)

Liang, W. et al. (2023) GPT detectors are biased against non-native English writers. _arXiv_ .
[htps://arxiv.org/abs/2304.02819](https://arxiv.org/abs/2304.02819)

Luccioni, A. et al. (2023) Power Hungry Processing: Watts Driving the Cost of AI Deployment? _arXiv_ .
[htps://arxiv.org/pdf/2311.16863](https://arxiv.org/pdf/2311.16863)

Mouton, C. et al. (2024) The Operational Risks of AI in Large-Scale Biological Attacks. _RAND_ .
[htps://www.rand.org/pubs/research_reports/RRA2977-2.html.](https://www.rand.org/pubs/research_reports/RRA2977-2.html)

Nicoletti, L. et al. (2023) Humans Are Biased. Generative Ai Is Even Worse. _Bloomberg_ .
[htps://www.bloomberg.com/graphics/2023-generatve-ai-bias/.](https://www.bloomberg.com/graphics/2023-generative-ai-bias/)

National Institute of Standards and Technology (2024) _Adversarial Machine Learning: A Taxonomy and_
_Terminology of Attacks and Mitigations_ [htps://csrc.nist.gov/pubs/ai/100/2/e2023/fnal](https://csrc.nist.gov/pubs/ai/100/2/e2023/final)

National Institute of Standards and Technology (2023) _AI Risk Management Framework._
[htps://www.nist.gov/itl/ai-risk-management-framework](https://www.nist.gov/itl/ai-risk-management-framework)

National Institute of Standards and Technology (2023) _AI Risk Management Framework, Chapter 3: AI_
_Risks and Trustworthiness._
[htps://airc.nist.gov/AI_RMF_Knowledge_Base/AI_RMF/Foundatonal_Informaton/3-sec-characteristcs](https://airc.nist.gov/AI_RMF_Knowledge_Base/AI_RMF/Foundational_Information/3-sec-characteristics)

National Institute of Standards and Technology (2023) _AI Risk Management Framework, Chapter 6: AI_
_RMF Profiles_ . [htps://airc.nist.gov/AI_RMF_Knowledge_Base/AI_RMF/Core_And_Profles/6-sec-profle](https://airc.nist.gov/AI_RMF_Knowledge_Base/AI_RMF/Core_And_Profiles/6-sec-profile)

National Institute of Standards and Technology (2023) _AI Risk Management Framework, Appendix A:_
_Descriptions of AI Actor Tasks_ .
[htps://airc.nist.gov/AI_RMF_Knowledge_Base/AI_RMF/Appendices/Appendix_A#:~:text=AI%20actors%](https://airc.nist.gov/AI_RMF_Knowledge_Base/AI_RMF/Appendices/Appendix_A#:%7E:text=AI%20actors%20in%20this%20category,data%20providers%2C%20system%20funders%2C%20product)
[20in%20this%20category,data%20providers%2C%20system%20funders%2C%20product](https://airc.nist.gov/AI_RMF_Knowledge_Base/AI_RMF/Appendices/Appendix_A#:%7E:text=AI%20actors%20in%20this%20category,data%20providers%2C%20system%20funders%2C%20product)


56


National Institute of Standards and Technology (2023) _AI Risk Management Framework, Appendix B:_
_How AI Risks Differ from Traditional Software Risks_ .
[htps://airc.nist.gov/AI_RMF_Knowledge_Base/AI_RMF/Appendices/Appendix_B](https://airc.nist.gov/AI_RMF_Knowledge_Base/AI_RMF/Appendices/Appendix_B)

National Institute of Standards and Technology (2023) _AI RMF Playbook_ .
[htps://airc.nist.gov/AI_RMF_Knowledge_Base/Playbook](https://airc.nist.gov/AI_RMF_Knowledge_Base/Playbook)

National Institue of Standards and Technology (2023) _Framing Risk_
[htps://airc.nist.gov/AI_RMF_Knowledge_Base/AI_RMF/Foundatonal_Informaton/1-sec-risk](https://airc.nist.gov/AI_RMF_Knowledge_Base/AI_RMF/Foundational_Information/1-sec-risk)

National Institute of Standards and Technology (2023) _The Language of Trustworthy AI: An In-Depth_
_Glossary of Terms_ [htps://airc.nist.gov/AI_RMF_Knowledge_Base/Glossary](https://airc.nist.gov/AI_RMF_Knowledge_Base/Glossary)

National Institue of Standards and Technology (2022) _Towards a Standard for Identifying and Managing_
_Bias in Artificial Intelligence_ [htps://www.nist.gov/publicatons/towards-standard-identfying-and-](https://www.nist.gov/publications/towards-standard-identifying-and-managing-bias-artificial-intelligence)
[managing-bias-artfcial-intelligence](https://www.nist.gov/publications/towards-standard-identifying-and-managing-bias-artificial-intelligence)

Northcutt, C. et al. (2021) Pervasive Label Errors in Test Sets Destabilize Machine Learning Benchmarks.
_arXiv_ . [htps://arxiv.org/pdf/2103.14749](https://arxiv.org/pdf/2103.14749)

OECD (2023) "Advancing accountability in AI: Governing and managing risks throughout the lifecycle for
trustworthy AI", _OECD Digital Economy Papers_, No. 349, OECD Publishing, Paris.
[htps://doi.org/10.1787/2448f04b-en](https://doi.org/10.1787/2448f04b-en)

OECD (2024) "Defining AI incidents and related terms" _OECD Artificial Intelligence Papers_, No. 16, OECD
Publishing, Paris. [htps://doi.org/10.1787/d1a8d965-en](https://doi.org/10.1787/d1a8d965-en)

[OpenAI (2023) GPT-4 System Card. htps://cdn.openai.com/papers/gpt-4-system-card.pdf](https://cdn.openai.com/papers/gpt-4-system-card.pdf)

OpenAI (2024) GPT-4 Technical Report. [htps://arxiv.org/pdf/2303.08774](https://arxiv.org/pdf/2303.08774)

Padmakumar, V. et al. (2024) Does writing with language models reduce content diversity? _ICLR_ .
[htps://arxiv.org/pdf/2309.05196](https://arxiv.org/pdf/2309.05196)

Park, P. et. al. (2024) AI deception: A survey of examples, risks, and potential solutions. Patterns, 5(5).
_arXiv_ . [htps://arxiv.org/pdf/2308.14752](https://arxiv.org/pdf/2308.14752)

Partnership on AI (2023) _Building a Glossary for Synthetic Media Transparency Methods, Part 1: Indirect_
_Disclosure_ . [htps://partnershiponai.org/glossary-for-synthetc-media-transparency-methods-part-1-](https://partnershiponai.org/glossary-for-synthetic-media-transparency-methods-part-1-indirect-disclosure/)
[indirect-disclosure/](https://partnershiponai.org/glossary-for-synthetic-media-transparency-methods-part-1-indirect-disclosure/)

Qu, Y. et al. (2023) Unsafe Diffusion: On the Generation of Unsafe Images and Hateful Memes From TextTo-Image Models. _arXiv_ . [htps://arxiv.org/pdf/2305.13873](https://arxiv.org/pdf/2305.13873)

Rafat, K. et al. (2023) Mitigating carbon footprint for knowledge distillation based deep learning model
compression. _PLOS One_ [. htps://journals.plos.org/plosone/artcle?id=10.1371/journal.pone.0285668](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0285668)

Said, I. et al. (2022) Nonconsensual Distribution of Intimate Images: Exploring the Role of Legal Atiudes
in Victimization and Perpetration. _Sage_ .
[htps://journals.sagepub.com/doi/full/10.1177/08862605221122834#bibr47-08862605221122834](https://journals.sagepub.com/doi/full/10.1177/08862605221122834#bibr47-08862605221122834)

Sandbrink, J. (2023) Artificial intelligence and biological misuse: Differentiating risks of language models
and biological design tools. _arXiv_ . [htps://arxiv.org/pdf/2306.13952](https://arxiv.org/pdf/2306.13952)


57


Satariano, A. et al. (2023) The People Onscreen Are Fake. The Disinformation Is Real. _New York Times_ .
[htps://www.nytmes.com/2023/02/07/technology/artfcial-intelligence-training-deepfake.html](https://www.nytimes.com/2023/02/07/technology/artificial-intelligence-training-deepfake.html)

Schaul, K. et al. (2024) Inside the secret list of websites that make AI like ChatGPT sound smart.
_Washington Post_ . [htps://www.washingtonpost.com/technology/interactve/2023/ai-chatbot-learning/](https://www.washingtonpost.com/technology/interactive/2023/ai-chatbot-learning/)

Scheurer, J. et al. (2023) Technical report: Large language models can strategically deceive their users
when put under pressure. _arXiv._ htps://arxiv.org/abs/2311.07590

Shelby, R. et al. (2023) Sociotechnical Harms of Algorithmic Systems: Scoping a Taxonomy for Harm
Reduction. _arXiv_ . [htps://arxiv.org/pdf/2210.05791](https://arxiv.org/pdf/2210.05791)

Shevlane, T. et al. (2023) Model evaluation for extreme risks. _arXiv_ . [htps://arxiv.org/pdf/2305.15324](https://arxiv.org/pdf/2305.15324)

Shumailov, I. et al. (2023) The curse of recursion: training on generated data makes models forget. _arXiv_ .
[htps://arxiv.org/pdf/2305.17493v2](https://arxiv.org/pdf/2305.17493v2)

Smith, A. et al. (2023) Hallucination or Confabulation? Neuroanatomy as metaphor in Large Language
Models. _PLOS Digital Health_ .
[htps://journals.plos.org/digitalhealth/artcle?id=10.1371/journal.pdig.0000388](https://journals.plos.org/digitalhealth/article?id=10.1371/journal.pdig.0000388)

Soice, E. et al. (2023) Can large language models democratize access to dual-use biotechnology? _arXiv_ .
[htps://arxiv.org/abs/2306.03809](https://arxiv.org/abs/2306.03809)

Solaiman, I. et al. (2023) The Gradient of Generative AI Release: Methods and Considerations. _arXiv._
[htps://arxiv.org/abs/2302.04844](https://arxiv.org/abs/2302.04844)

Staab, R. et al. (2023) Beyond Memorization: Violating Privacy via Inference With Large Language
Models. _arXiv_ . [htps://arxiv.org/pdf/2310.07298](https://arxiv.org/pdf/2310.07298)

Stanford, S. et al. (2023) Whose Opinions Do Language Models Reflect? _arXiv_ .
[htps://arxiv.org/pdf/2303.17548](https://arxiv.org/pdf/2303.17548)

Strubell, E. et al. (2019) Energy and Policy Considerations for Deep Learning in NLP. _arXiv_ .
[htps://arxiv.org/pdf/1906.02243](https://arxiv.org/pdf/1906.02243)

The White House (2016) Circular No. A-130, Managing Information as a Strategic Resource.
htps://www.whitehouse.gov/wp[content/uploads/legacy_drupal_fles/omb/circulars/A130/a130revised.pdf](https://www.whitehouse.gov/wp-content/uploads/legacy_drupal_files/omb/circulars/A130/a130revised.pdf)

The White House (2023) Executive Order on the Safe, Secure, and Trustworthy Development and Use of
Artificial Intelligence. [htps://www.whitehouse.gov/briefng-room/presidental-](https://www.whitehouse.gov/briefing-room/presidential-actions/2023/10/30/executive-order-on-the-safe-secure-and-trustworthy-development-and-use-of-artificial-intelligence/)
[actons/2023/10/30/executve-order-on-the-safe-secure-and-trustworthy-development-and-use-of-](https://www.whitehouse.gov/briefing-room/presidential-actions/2023/10/30/executive-order-on-the-safe-secure-and-trustworthy-development-and-use-of-artificial-intelligence/)
[artfcial-intelligence/](https://www.whitehouse.gov/briefing-room/presidential-actions/2023/10/30/executive-order-on-the-safe-secure-and-trustworthy-development-and-use-of-artificial-intelligence/)

The White House (2022) Roadmap for Researchers on Priorities Related to Information Integrity
Research and Development. [htps://www.whitehouse.gov/wp-content/uploads/2022/12/Roadmap-](https://www.whitehouse.gov/wp-content/uploads/2022/12/Roadmap-Information-Integrity-RD-2022.pdf?)
[Informaton-Integrity-RD-2022.pdf?](https://www.whitehouse.gov/wp-content/uploads/2022/12/Roadmap-Information-Integrity-RD-2022.pdf?)

Thiel, D. (2023) Investigation Finds AI Image Generation Models Trained on Child Abuse. _Stanford Cyber_
_Policy Center_ . [htps://cyber.fsi.stanford.edu/news/investgaton-fnds-ai-image-generaton-models-](https://cyber.fsi.stanford.edu/news/investigation-finds-ai-image-generation-models-trained-child-abuse)
[trained-child-abuse](https://cyber.fsi.stanford.edu/news/investigation-finds-ai-image-generation-models-trained-child-abuse)


58


Tirrell, L. (2017) Toxic Speech: Toward an Epidemiology of Discursive Harm. _Philosophical Topics, 45(2)_,
139-162. [htps://www.jstor.org/stable/26529441](https://www.jstor.org/stable/26529441)

Tufekci, Z. (2015) Algorithmic Harms Beyond Facebook and Google: Emergent Challenges of
Computational Agency. _Colorado Technology Law Journal_ . [htps://ctlj.colorado.edu/wp-](https://ctlj.colorado.edu/wp-content/uploads/2015/08/Tufekci-final.pdf)
[content/uploads/2015/08/Tufekci-fnal.pdf](https://ctlj.colorado.edu/wp-content/uploads/2015/08/Tufekci-final.pdf)

Turri, V. et al. (2023) Why We Need to Know More: Exploring the State of AI Incident Documentation
Practices. _AAAI/ACM Conference on AI, Ethics, and Society_ .
[htps://dl.acm.org/doi/fullHtml/10.1145/3600211.3604700](https://dl.acm.org/doi/fullHtml/10.1145/3600211.3604700)

Urbina, F. et al. (2022) Dual use of artificial-intelligence-powered drug discovery. _Nature Machine_
_Intelligence_ . [htps://www.nature.com/artcles/s42256-022-00465-9](https://www.nature.com/articles/s42256-022-00465-9)

Wang, X. et al. (2023) Energy and Carbon Considerations of Fine-Tuning BERT. _ACL Anthology_ .
[htps://aclanthology.org/2023.fndings-emnlp.607.pdf](https://aclanthology.org/2023.findings-emnlp.607.pdf)

Wang, Y. et al. (2023) Do-Not-Answer: A Dataset for Evaluating Safeguards in LLMs. _arXiv_ .
[htps://arxiv.org/pdf/2308.13387](https://arxiv.org/pdf/2308.13387)

Wardle, C. et al. (2017) Information Disorder: Toward an interdisciplinary framework for research and
policy making. _Council of Europe._ [htps://rm.coe.int/informaton-disorder-toward-an-interdisciplinary-](https://rm.coe.int/information-disorder-toward-an-interdisciplinary-framework-for-researc/168076277c)
[framework-for-researc/168076277c](https://rm.coe.int/information-disorder-toward-an-interdisciplinary-framework-for-researc/168076277c)

Weatherbed, J. (2024) Trolls have flooded X with graphic Taylor Swift AI fakes. _The Verge_ .
[htps://www.theverge.com/2024/1/25/24050334/x-twiter-taylor-swif-ai-fake-images-trending](https://www.theverge.com/2024/1/25/24050334/x-twitter-taylor-swift-ai-fake-images-trending)

Wei, J. et al. (2024) Long Form Factuality in Large Language Models. _arXiv._
[htps://arxiv.org/pdf/2403.18802](https://arxiv.org/pdf/2403.18802)

Weidinger, L. et al. (2021) Ethical and social risks of harm from Language Models. _arXiv_ .
[htps://arxiv.org/pdf/2112.04359](https://arxiv.org/pdf/2112.04359)

Weidinger, L. et al. (2023) Sociotechnical Safety Evaluation of Generative AI Systems. _arXiv_ .
[htps://arxiv.org/pdf/2310.11986](https://arxiv.org/pdf/2310.11986)

Weidinger, L. et al. (2022) Taxonomy of Risks posed by Language Models. _FAccT ’22_ .
[htps://dl.acm.org/doi/pdf/10.1145/3531146.3533088](https://dl.acm.org/doi/pdf/10.1145/3531146.3533088)

West, D. (2023) AI poses disproportionate risks to women. _Brookings._
[htps://www.brookings.edu/artcles/ai-poses-disproportonate-risks-to-women/](https://www.brookings.edu/articles/ai-poses-disproportionate-risks-to-women/)

Wu, K. et al. (2024) How well do LLMs cite relevant medical references? An evaluation framework and
analyses. _arXiv_ . [htps://arxiv.org/pdf/2402.02008](https://arxiv.org/pdf/2402.02008)

Yin, L. et al. (2024) OpenAI’s GPT Is A Recruiter’s Dream Tool. Tests Show There’s Racial Bias. _Bloomberg_ .
[htps://www.bloomberg.com/graphics/2024-openai-gpt-hiring-racial-discriminaton/](https://www.bloomberg.com/graphics/2024-openai-gpt-hiring-racial-discrimination/)

Yu, Z. et al. (March 2024) Don’t Listen To Me: Understanding and Exploring Jailbreak Prompts of Large
Language Models. _arXiv_ . [htps://arxiv.org/html/2403.17336v1](https://arxiv.org/html/2403.17336v1)

Zaugg, I. et al. (2022) Digitally-disadvantaged languages. _Policy Review._
[htps://policyreview.info/pdf/policyreview-2022-2-1654.pdf](https://policyreview.info/pdf/policyreview-2022-2-1654.pdf)


59


Zhang, Y. et al. (2023) Human favoritism, not AI aversion: People’s perceptions (and bias) toward
generative AI, human experts, and human–GAI collaboration in persuasive content generation. _Judgment_
_and Decision Making_ . [htps://www.cambridge.org/core/journals/judgment-and-decision-](https://www.cambridge.org/core/journals/judgment-and-decision-making/article/human-favoritism-not-ai-aversion-peoples-perceptions-and-bias-toward-generative-ai-human-experts-and-humangai-collaboration-in-persuasive-content-generation/419C4BD9CE82673EAF1D8F6C350C4FA8)
[making/artcle/human-favoritsm-not-ai-aversion-peoples-perceptons-and-bias-toward-generatve-ai-](https://www.cambridge.org/core/journals/judgment-and-decision-making/article/human-favoritism-not-ai-aversion-peoples-perceptions-and-bias-toward-generative-ai-human-experts-and-humangai-collaboration-in-persuasive-content-generation/419C4BD9CE82673EAF1D8F6C350C4FA8)
[human-experts-and-humangai-collaboraton-in-persuasive-content-](https://www.cambridge.org/core/journals/judgment-and-decision-making/article/human-favoritism-not-ai-aversion-peoples-perceptions-and-bias-toward-generative-ai-human-experts-and-humangai-collaboration-in-persuasive-content-generation/419C4BD9CE82673EAF1D8F6C350C4FA8)
[generaton/419C4BD9CE82673EAF1D8F6C350C4FA8](https://www.cambridge.org/core/journals/judgment-and-decision-making/article/human-favoritism-not-ai-aversion-peoples-perceptions-and-bias-toward-generative-ai-human-experts-and-humangai-collaboration-in-persuasive-content-generation/419C4BD9CE82673EAF1D8F6C350C4FA8)

Zhang, Y. et al. (2023) Siren’s Song in the AI Ocean: A Survey on Hallucination in Large Language Models.
_arXiv_ . [htps://arxiv.org/pdf/2309.01219](https://arxiv.org/pdf/2309.01219)

Zhao, X. et al. (2023) Provable Robust Watermarking for AI-Generated Text. _Semantic Scholar_ .
[htps://www.semantcscholar.org/paper/Provable-Robust-Watermarking-for-AI-Generated-Text-Zhao-](https://www.semanticscholar.org/paper/Provable-Robust-Watermarking-for-AI-Generated-Text-Zhao-Ananth/75b68d0903af9d9f6e47ce3cf7e1a7d27ec811dc)
[Ananth/75b68d0903af9d9f6e47ce3cf7e1a7d27ec811dc](https://www.semanticscholar.org/paper/Provable-Robust-Watermarking-for-AI-Generated-Text-Zhao-Ananth/75b68d0903af9d9f6e47ce3cf7e1a7d27ec811dc)


60
