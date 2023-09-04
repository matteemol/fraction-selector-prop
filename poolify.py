from fpdf import FPDF
from fpdf.fonts import FontFace
# Create objects (column fractions) with info from a CSV file
# Fraction ID, Total Area, % Purity
# Choose all the fractions that meet a specific criteria
# Objects must have the 3 data items from CSV + information about selection

class Fraction:
    '''
    To create each portion of the chromatographic separation (fraction)
    with its corresponding attributes and values to compute

    '''
    def __init__(self, HU, a_per, a_tot):
        self.HU = HU
        self.a_per = float(a_per)
        self.a_tot = float(a_tot)
        self.all_peak = a_tot / a_per
        self.collect = True
        self.percent_product = 0
        self.discarded_by = "-"


class PDF(FPDF):
    def header(self):
        # Rendering logo:
        self.image("img/logo.jpg", 150, 8, 33)
        # Setting font: helvetica bold 15
        self.set_font("helvetica", "B", 15)
        # Moving cursor to the right:
        self.cell(30)
        # Printing title:
        self.cell(80, 10, "Fraction selection result", border=1, align="C")
        # Performing a line break:
        self.ln(20)

    def footer(self):
        # Position cursor at 1.5 cm from bottom:
        self.set_y(-15)
        # Setting font: helvetica italic 8
        self.set_font("helvetica", "I", 8)
        # Printing page number:
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", align="C")

    def section_title(self, label):
        # Setting font: helvetica 12
        self.set_font("helvetica", "", 12)
        # Setting background color
        self.set_fill_color(167, 167, 167)
        # Performing a line break:
        self.ln(4)
        # Printing section title:
        self.cell(0, 7, f"{label}", new_x="LMARGIN", new_y="NEXT",
            align="L", fill=True)
        # Performing a line break:
        self.ln(4)

def doit(sample, hu_list, aper_list, atot_list, input_data):
# Create a dictionary where the fractions are listed keeping the
# corresponding HU as unique IDs
    print("doit call received")
    fractions_dict = createfractions(hu_list, aper_list, atot_list)

# Calculate and set the total % quantity for each fraction, with respect
# to the total product in all the fractions
    total_product_percent(fractions_dict, atot_list)

# Set targets & rules for the calculations. This will further be loaded
# with a configuration file.

    rules = [(70, 2), (70,100), (80, 2), (80, 100)]
    target_recovery = 50
    target_purity = 94

# Core function of the program: choose the fractions according to the
# targets & rules set above
    pur, rec, rul = optimize(fractions_dict, rules, target_purity, target_recovery)

# Create a list to store the HUs of the fractions that must be mixed together
    pooled_list = []
    for i in fractions_dict:
        if fractions_dict[i].collect == True:
            pooled_list.append(fractions_dict[i].HU)
#    print(f'HUs that must be pooled are: {pooled_list}')

##
# Fourth part: results output
##
# Print results
#    print(f'Combined purity: {pur}')
#    print(f'Total recovery: {rec}')
#    print(f'Last rule applied: {rul}')

# fpdf uses a tuple of tuples as Table data. The folowing code is to transform the available data into a tuple.
    list_of_tuples = [("Fraction", "Area %", "Area (Absolute)", "% Product", "Discarded by rule")]

    for i in input_data:
        i.append(f"{fractions_dict[int(i[0])].percent_product}")
        i.append(f"{fractions_dict[int(i[0])].discarded_by}")
        list_of_tuples.append(tuple(i))

    input_data_tuples = tuple(list_of_tuples)

# Unpack sample data for PDF

    (batch_record, col_num, num_of_fractions) = sample

    print(batch_record)
    print(col_num)
    print(num_of_fractions)
    
# Create the PDF object
    pdf = PDF()
    pdf.add_page()
    pdf.set_font("helvetica", size=10)
    pdf.section_title("Sample identification")
    pdf.cell(0, 10, f"Batch Record: {batch_record}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 10, f"Column Number: {col_num}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 10, f"Number of fractions: {num_of_fractions}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 10, f"Set of rules: {rules}", new_x="LMARGIN", new_y="NEXT")
    pdf.section_title("Fraction data")
    pdf.set_draw_color(0, 0, 0)
    pdf.set_line_width(0.3)
    pdf.set_fill_color(255, 255, 255)
    headings_style = FontFace(emphasis="BOLD", color=(217, 217, 217), fill_color=(0, 102, 153))
    with pdf.table(
        borders_layout="NO_HORIZONTAL_LINES",
        cell_fill_mode='NONE',
        col_widths=(20, 20, 40, 30, 40),
        headings_style=headings_style,
        line_height=6,
        text_align=("CENTER", "CENTER", "CENTER", "CENTER", "CENTER"),
        width=150,
    ) as table:
        for data_row in input_data_tuples:

            if data_row[0] != "Fraction":
                if int(data_row[0]) in pooled_list:
                    pdf.set_fill_color(98, 198, 155)
                else:
                    pdf.set_fill_color(255, 255, 255)

            row = table.row()
            for datum in data_row:
                row.cell(str(datum))
            pdf.set_fill_color(255, 255, 255)

    pdf.section_title("Result")
    pdf.cell(0, 10, f"Fractions {pooled_list} must be selected", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 10, f"Combined purity: {pur}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 10, f"Total recovery: {rec}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 10, f"Last rule applied: {rul}", new_x="LMARGIN", new_y="NEXT")
    pdf.output("bulletin.pdf")


def createfractions(hu_l, aper_l, atot_l):
    '''
    Generates a dictionary where the keys are taken from the hu_list
    list and the values are Fraction classes, created by this function

      Parameters:
        hu_l: list of HUs of all the fractions
        aper_l: list of % area of the product in each fraction
        atot_l: list of the absolute (total) area of the product in
                the fraction

      Returns: a dictionary with keys = HU, values = Fraction classes
    '''
    f_dict = {hu_l[i]: Fraction(hu_l[i], aper_l[i], atot_l[i]) for i in range(len(hu_l))}
    return f_dict


def total_product_percent(f_d, a_list):
    '''
    Calculates the % product of each fraction and sets it's
    corresponding attribute

      Parameters:
        f_d (dict): the dictionary with all the fractions
        a_list (list): list with the total product area of each fraction

      Returns:
        No output value. This function sets the "percent_product"
        attribute of each fraction in the f_d dict to the calculated
        value (portion of the total product area)
    '''
    sum_area = sum(a_list)
    for i in f_d:
        f_d[i].percent_product = round(float(f_d[i].a_tot / sum_area) * 100, 2)


def unselect(f_d, rule):
    '''
    Compares the area percent (aper) and percent product (% in fraction)
    of each fraction from the f_d dict according to a rule.
    If any of these values is lower than the required by the rule, then
    the fraction.collect attribute is assigned a 'False' value (i.e: the
    fraction is not considered for the pool)

      Parameters:
        f_d (dict): dictionary with all the fractions
        rule (tuple): tuple of two (pair) values to be used as limit
        in the  function to compare the samples with.

      Returns: no values are returned. This function modifies the
      "collect" attribute of each fraction in the passed dictionary
    '''
    min_per, min_area = rule # rule unpacking
    for i in f_d:
        if f_d[i].a_per < float(min_per):
            if f_d[i].percent_product < float(min_area):
                if f_d[i].collect == True:
                    f_d[i].collect = False
                    f_d[i].discarded_by = rule


def purity(f_d):
    '''
    Calculates the combined purity of the fractions that have the
    attribute "collect" = True

      Parameters:
        f_d: the dictionary of all the fractions

      Returns: a number (float) that represents the purity of the
        combined/pooled fractions
    '''
    p_areas = 0
    all_areas = 0
    for i in f_d:
        if f_d[i].collect == True:
            p_areas += f_d[i].a_tot
            all_areas += f_d[i].all_peak
    return float('{:.1f}'.format(round(p_areas / all_areas, 1)))


def recovery(f_d):
    '''
    Calculates the recovery % of the fractions that have the
    attribute "collect" = True

      Parameters:
        f_d: the dictionary of all the fractions

      Returns: a number (float) that represents the recovery %
        of the combined/pooled fractions
    '''
    total = 0
    selected = 0
    for i in f_d:
        total += f_d[i].a_tot
        if f_d[i].collect == True:
            selected += f_d[i].a_tot
    return float('{:.1f}'.format(round(100 * selected / total, 1)))


def optimize(f_d, rules, t_pur, t_rec):
    '''
    Compares each fraction data with the limits established by the rules

      Parameters:
        f_d (dict): dictionary with all the fractions
        rules (list of tuples): list of rules to compare with
        t_pur (float): target purity value
        t_rec (float): target recovery value

        Returns: a tuple of 3 values: the calculated purity, recovery
          and the maximum rule required to achieve the target purity
          in the pool.
    '''
# First run, calculate purity and recovery with all the fractions
    i = 0
    p = purity(f_d)
    r = recovery(f_d)

    while i < len(rules):
# if the targets are met, return the values
        if p >= t_pur and r >= t_rec:
                return p, r, i
# if the target is not met, proceed with unselecting fractions
# according to the next rule
        unselect(f_d, rules[i])
# calculate the new purity and recovery values for the new set of
# fractions
        p = purity(f_d)
        r = recovery(f_d)
        i += 1

# if after following all the rules, the target purity is still not met,
# proceed unselecting fractions from the lowest to the highest
# % product (aper) until the target PURITY is achieved.
    while p < t_pur:
        unselect_low_purity(f_d)
        p = purity(f_d)
        r = recovery(f_d)
        i = 5

# after reaching the target purity, the calculated recovery is checked
# to see if it meets the criteria (higher than the t_rec target).
# If it's not acceptable, the program exits with no further
# calculations with a message reporting this issue.
    if r < t_rec:
#        exit(f'Target recovery of 80 % not met.')
        raise Exception("Target recovery of 80 % not met")

# Finally, if the target purity and recover are met, the function
# returns these values, together with the number of the last rule
# applied
    return p, r, i


def unselect_low_purity(f_d):
    '''
    Looks up for the lowest area percent (aper) in the pool and sets the
    fraction.collect attribute to 'False' value (i.e: the fraction
    is not further considered for the pool).

      Parameters:
        f_d (dict): dictionary with all the fractions information

        Returns: no values are returned. The .collect attribute of the
          fraction with the lowest area percent is set to "False" and
          it is discarded.
    '''
    lp_hu = []
    lp_aper = []
    lp_pp = []
    for i in f_d:
        if f_d[i].collect:
            lp_hu.append(f_d[i].HU)
            lp_aper.append(float(f_d[i].a_per))
            lp_pp.append(float(f_d[i].percent_product))

    f_d[lp_hu[lp_aper.index(min(lp_aper))]].collect = False
    f_d[lp_hu[lp_aper.index(min(lp_aper))]].discarded_by = "5th rule"


if __name__ == "__main__":
    doit()
