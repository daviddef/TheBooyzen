/* Who belongs to whom, and on whose word.
 *
 * Every household below is a claim with a source. The `via` on a household is
 * how the marriage is known; the `via` on a child is how THAT child's place in
 * it is known. They differ often, which is the point of recording them apart.
 *
 *   line  the archive's own direct line, argued on /direct-line/
 *   doc   stated in a record this archive has read
 *   inf   inferred from a record — the record does not say it
 *   tree  from the family tree, unverified
 *
 * Names must match site/src/data/people.js exactly. Where a name is carried by
 * more than one person, add "|token" and the token must appear in that person's
 * birth or death string: "Petrus Jacobus Booysen|1812".
 */
export const families = [
  { h: "Gerthardus Lodewikus Booysen", w: "Magdelena Elisabeth de Beer", via: "doc",
    why: "Named together in line 3 of their son's 1876 Sterfkennis — the oldest document this archive has read.",
    src: ["The 1876 Sterfkennis", "/documents/#sterfkennis-1876"],
    kids: [{ n: "Petrus Jacobus Booysen|1788", via: "line" }] },

  { h: "Petrus Jacobus Booysen|1788", w: "Anna Maria van der Merwe", via: "tree",
    why: "Married 1805 at Graaff-Reinet, on the family tree. She died before March 1825 and he died a widower in 1876, so at least one later marriage is missing from this row.",
    warn: "The 1876 notice lists eight children and names no mother for any of them. They are drawn under this marriage because it is the only one recorded — not because the document says so.",
    src: ["The 1876 Sterfkennis", "/documents/#sterfkennis-1876"],
    kids: [
      { n: "David Schalk Booijsen", via: "doc" },
      { n: "Magdalena Johanna Booijsen", via: "doc" },
      { n: "Petrus Jacobus Booysen|1812", via: "line" },
      { n: "Anna Eliezabet Booijsen", via: "doc" },
      { n: "Jan Gerthardus Lodewikus Booijsen", via: "doc" },
      { n: "Eliezabet Cornelia Booijsen", via: "doc" },
      { n: "Hendrik Stefanus Booijsen", via: "doc" },
      { n: "Anna Maria Booijsen", via: "doc" }] },

  { h: "Petrus Jacobus Booysen|1812", w: "Johanna Catharina Mountjoy", via: "doc",
    why: "Married at Cradock 4 November 1838. He signed her death notice in 1863; it names her parents and their eight surviving children.",
    src: ["The 1863 death notice", "/documents/"],
    kids: [
      { n: "Jacobus Nicholas Booysen", via: "doc" },
      { n: "Johanna Catharina Booysen", via: "doc" },
      { n: "Petrus Jacobus Booysen|1839", via: "doc" },
      { n: "Anna Catharina Booysen", via: "doc" },
      { n: "David Schalk Booysen|1848", via: "doc" },
      { n: "Willem Hermanus “William Henry” Booyzen", via: "line" },
      { n: "Magdalena Johanna Francina Booysen", via: "doc" },
      { n: "Jan Gerhardus Lodewicus Booysen", via: "doc" },
      { n: "Jacoba Catharina Booysen", via: "doc" }] },

  { h: "Petrus Jacobus Booysen|1812", w: "Johanna Margaritha Pretorius", via: "doc",
    why: "The second marriage, unnamed on his own 1884 death notice and finally named by a christening: the 1870 Doop Register enters the parents as “Petrus Jacobus Booyzen en Johanna Margaritha Pretorius”.",
    src: ["The second wife, named at last", "/documents/"],
    kids: [
      { n: "Gerrit Jacobus Booÿsen", via: "doc" },
      { n: "Stephanus Francois Booyzen", via: "inf" }] },

  { h: "Gerrit Jacobus Booÿsen", w: "Isabella Frederika Coetsee", via: "doc",
    why: "Married at Middelburg, 23 March 1896.",
    kids: [{ n: "Petrus Jacobus Booyzen|1904", via: "doc" }] },

  { h: "Willem Hermanus “William Henry” Booyzen", w: "Catherine Maria Sophia “Kathleen” Barry", via: "doc",
    why: "Married 22 December 1879 — the marriage register that carries the disputed signature.",
    src: ["The name", "/name/"],
    kids: [
      { n: "John Barry Booyzen", via: "doc" },
      { n: "Willem Hermanus Booyzen of Indwe", via: "inf" },
      { n: "David Kolbe Booyzen", via: "tree" },
      { n: "Henry James Booyzen", via: "tree" },
      { n: "Gertruida Alexandra Booyzen", via: "tree" },
      { n: "Johanna Catharina Booyzen|1889", via: "doc" },
      { n: "Catharina Maria Sophia Booysen", via: "doc" },
      { n: "George Downing Mountjoy Booyzen", via: "line" }] },

  { h: "Willem Hermanus Booyzen of Indwe", w: "Susanna Adriana Roodt", via: "doc",
    why: "Married at Indwe on 21 September 1908, certificate 13 — he 22 and a mijnwerker, she 16 and her parents consenting, both living at Dugmore Mijn.",
    src: ["Indwe, 1907–1910", "/documents/#indwe-1907"],
    kids: [{ n: "Willem Hermanus Booyzen of Dugmore", via: "doc" }] },

  { h: "Willem Hermanus Booyzen of Indwe", w: "Catharina Maria Elizabeth Roodt", via: "doc",
    why: "Not a marriage. She is named as the mother on the Indwe baptism of 22 September 1910, and the entry is marked onecht. She was confirmed in the same class as him and as Susanna Adriana Roodt on 31 May 1907.",
    src: ["Indwe, 1907–1910", "/documents/#indwe-1907"],
    kids: [{ n: "Catharina Willemina Levina Booyzen", via: "doc" }] },

  { h: "George Downing Mountjoy Booyzen", w: "Anna Johanna Maria Pretorius", via: "doc",
    why: "Married at Vereeniging, 30 December 1924 — a tree nurseryman and a girl of eighteen who were first cousins once removed.",
    src: ["The cousin marriage", "/cousins/"],
    kids: [
      { n: "Willem Hermanus “Willy” Booyzen", via: "doc" },
      { n: "Margaretha Wilhelmina Elizabeth “Maggie” Booyzen", via: "doc" },
      { n: "Catherine Mary Sophia Booyzen", via: "line" },
      { n: "Anna Johanna Maria Booyzen (Vermaak)", via: "doc" },
      { n: "Georgina Jeanette Booyzen (Boshoff)", via: "doc" },
      { n: "Petrus Jacobus “Piet” Booyzen", via: "doc" },
      { n: "Gertrude Elizabeth Booyzen", via: "doc" },
      { n: "Gertrude Booyzen", via: "doc" }] },

  { h: "Nuno Fernando Lerena", w: "Catherine Mary Sophia Booyzen", via: "doc",
    why: "Married 15 January 1949 at St Joseph's, Mayfair — the hinge to the Lerena archive.",
    kids: [] },

  { h: "Petrus Jacobus Pretorius", w: "Margarietha Wilhelmina Elizabeth Barry", via: "doc",
    why: "Named together as parents in the 1906 Gereformeerde Kerk baptism register, and again on their daughter's 1944 Sterfkennis with their address — 96 James Street, Germiston.",
    src: ["1944, the parents line filled in", "/documents/"],
    kids: [{ n: "Anna Johanna Maria Pretorius", via: "doc" }] },

  { h: "Stephanus Francois Booyzen", w: "Beatrix Magdalena Catharina Boshoff", via: "doc",
    why: "Married at Mossel Bay. She signed his 1940 Sterfkennis and could not name his parents.",
    kids: [] },

  { h: "Willem Hermanus Pieterzen|bef. 1817", w: "Anna Catharina Sleer", via: "doc",
    why: "Her first husband. The 1817 marriage register calls her “widow of Harmanus Pieterze”; the 1840 death notice calls him “William Pietersen”.",
    src: ["Where the blank begins", "/documents/"],
    kids: [{ n: "Willem Hermanus Pieterzen|—", via: "doc" }] },

  { h: "James Montjoy", w: "Anna Catharina Sleer", via: "doc",
    why: "Married at Graaff-Reinet, 9 March 1817 — on a page where the clerk recorded everyone else's origin and left his blank.",
    src: ["The 1817 marriage register", "/documents/"],
    kids: [
      { n: "Thomas Jacobus Mountjoy", via: "doc" },
      { n: "Johanna Catharina Mountjoy", via: "line" },
      { n: "Jacoba Catharina Mountjoy", via: "doc" },
      { n: "George Mountjoy|1823", via: "doc" },
      { n: "James Mountjoy|1826", via: "doc" }] },

  { h: "George Mountjoy|1823", w: "Maria Sophia Botha", via: "doc",
    why: "Married at Cradock, 20 August 1848, certificate 735. Thirteen children.",
    kids: [{ n: "Hercules Johannes Mountjoy", via: "doc" }] },

  { h: "Hercules Johannes Mountjoy", w: "Maria Sophia van Niekerk", via: "doc",
    why: "Married at Dordrecht, 8 October 1888, aged 22 and 20.",
    src: ["Two grandparents at a font", "/documents/"],
    kids: [{ n: "George Mountjoy|1889", via: "doc" }] },

  { h: "Jan Dirk Abram Frans van Niekerk", w: "Carolina Deybella Margrietta Alletta Botha", via: "doc",
    why: "He signed her death notice at Dordrecht on 29 December 1902 as “nablyvende echtgenoot”. It lists eleven children.",
    src: ["The 1902 van Niekerk notice", "/documents/#van-niekerk-1902"],
    kids: [{ n: "Maria Sophia van Niekerk", via: "doc" }] },

  { h: "James Jonathan Mountjoy", w: "Maria Louisa Bertha Kumm", via: "doc",
    why: "Married in community of property at Dordrecht. Their two death notices were written on the same afternoon in February 1938, hers three and a half years late.",
    src: ["Barkly East, 1938", "/documents/#mountjoy-58379"],
    kids: [
      { n: "George Mountjoy of Barkly East", via: "doc" },
      { n: "Maria Sophia Diesel", via: "doc" },
      { n: "Annie Louisa Nepgen", via: "doc" },
      { n: "Ellen Sophia Schmidt", via: "doc" },
      { n: "Charles Mountjoy", via: "doc" },
      { n: "James John Mountjoy the younger", via: "doc" },
      { n: "Emma Jane Mountjoy", via: "doc" },
      { n: "Mathilda Elizabeth Shooter", via: "doc" },
      { n: "Lena Millie Frachet", via: "doc" },
      { n: "Louisa Elizabeth Diesel", via: "doc" }] },

  { h: "Ferdinand Kumm", w: null, via: "tree",
    why: "Entered as her father on the family tree. His own 1903 death notice at Stutterheim is the document an external source mistook for James Jonathan's.",
    kids: [{ n: "Maria Louisa Bertha Kumm", via: "tree" }] },

  { h: null, w: "Louisa Elizabeth Diesel", via: "doc",
    why: "Married out of community of property to Evelyn Wilfred Diesel and dead fourteen years before her father. Her two children took her tenth share between them.",
    src: ["The distribution account", "/documents/#mountjoy-58379"],
    kids: [
      { n: "Gwendoline Diesel", via: "doc" },
      { n: "Aubrey Diesel", via: "doc" }] },

  { h: "Joseph Daschner", w: "Sophia Daschner", via: "doc",
    why: "Both named, and both “Deceased”, in line 3 of their son's 1942 death notice.",
    src: ["The 1942 Daschner notice", "/documents/#daschner-1942"],
    kids: [{ n: "Joseph Heinrich Daschner", via: "doc" }] },

  { h: "Joseph Heinrich Daschner", w: "Catharina Maria Sophia Booysen", via: "doc",
    why: "Married at Indwe — the same village where her father died in 1905. His 1942 notice enters her as “born Booyzen”, with a z.",
    src: ["The 1942 Daschner notice", "/documents/#daschner-1942"],
    kids: [
      { n: "Catherine Mary Sophia Daschner", via: "doc" },
      { n: "Joseph Charles Daschner", via: "doc" },
      { n: "Margaret Wilhelmina Elizabeth Jeanette van Jaarsveld", via: "doc" },
      { n: "William Herman Daschner", via: "doc" },
      { n: "Martha Magdeline van Deventer", via: "doc" },
      { n: "John Frederick Daschner", via: "doc" },
      { n: "Richard Peter Daschner", via: "doc" },
      { n: "Albert Alfred Daschner", via: "doc" },
      { n: "Edith Dorothy Daschner", via: "doc" },
      { n: "Henry James Daschner", via: "doc" },
      { n: "Yvonne Muriel Daschner", via: "doc" }] },

  { h: "John Barry", w: null, via: "tree",
    via_note: "disputed",
    why: "Entered on the family tree as the father. This archive does not accept the profile: it holds a Yorkshire farmer buried at Bilsdale on 3 January 1853 and a man who died at de Bruins Poort in the Cape five days later.",
    warn: "This is the archive's clearest example of two men merged into one profile. The link below him is drawn because the tree draws it, and for no other reason.",
    src: ["Disputed", "/disputed/"],
    kids: [{ n: "John Augustus Barry I", via: "tree" }] },

  { h: "John Augustus Barry I", w: "Margaretha Wilhelmina Elizabeth Mary Kolbe", via: "doc",
    why: "Married 1850. Both of their death notices survive, and the two disagree about the date he died.",
    src: ["The Barrys", "/barry/"],
    kids: [
      { n: "Catherine Maria Sophia “Kathleen” Barry", via: "line" },
      { n: "Hendrik Nicholaas Barry", via: "doc" },
      { n: "Margarietha Wilhelmina Elizabeth Barry", via: "doc" },
      { n: "Dorothea Regina Barry", via: "doc" },
      { n: "James Henry Barry", via: "doc" },
      { n: "Richard Peter Barry", via: "doc" },
      { n: "Ruben Jacobus Josuah Barry", via: "doc" },
      { n: "Frederick Fortunatus Barry", via: "doc" },
      { n: "Kathleen Mary Barry", via: "doc" }] },

  { h: "Hendrik Nicholaas Barry", w: "Anna Johanna Maria Schoeman", via: "doc",
    why: "The second Barry–Schoeman link, and part of why the 1924 marriage was between cousins.",
    src: ["The cousin marriage", "/cousins/"], kids: [] },

  { h: "George Augustus Kolbe", w: "Margaret Downing", via: "doc",
    why: "Married 1819 — both were sixteen, and the Nautilus passenger roll of 1820 overstates both their ages by four years.",
    src: ["The Kolbes", "/kolbe/"],
    kids: [
      { n: "Margaretha Wilhelmina Elizabeth Mary Kolbe", via: "line" },
      { n: "Marian Kolbe", via: "doc" },
      { n: "Julia Kolbe", via: "doc" },
      { n: "Frederik Fortunatus Kolbe", via: "doc" },
      { n: "Peter Benjamin Kolbe", via: "doc" }] },

  { h: "Johan Gottlieb Kolbe", w: null, via: "doc",
    why: "A tailor of Conduit Street, Mayfair. Four independent documents call him John Gottlob; the family tree calls him Johan Gottlieb, and this archive follows the documents.",
    src: ["The Kolbes", "/kolbe/"],
    kids: [
      { n: "George Augustus Kolbe", via: "doc" },
      { n: "John Gottlob Kolbe", via: "doc" }] },

  { h: "David Schalk van der Merwe", w: "Jacoba Catharina Mountjoy", via: "doc",
    why: "Married at Cradock, 24 March 1838 — eight months before her sister married Petrus Jacobus Booysen in the same town.",
    src: ["The women", "/women/"], kids: [] },

  { h: "Ruben Schoeman", w: "Magdalena Johanna Botha", via: "doc",
    why: "Named together on the 1901 marriage record kept in a rebel's house under martial law.",
    src: ["The documents", "/documents/"], kids: [] },

  { h: "John Paul Downing", w: null, via: "doc",
    why: "Margaret's father.",
    kids: [{ n: "Margaret Downing", via: "doc" }] },
];
