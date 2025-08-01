/**
 * Utility functions for mapping ingredients to appropriate food category icons
 */

export interface FoodCategory {
  id: string;
  label: string;
  icon: string;
  color: string;
}

export const FOOD_CATEGORIES: FoodCategory[] = [
  { id: 'produce', label: 'Produce', icon: '🥬', color: '#4ADE80' },
  { id: 'dairy', label: 'Dairy', icon: '🥛', color: '#60A5FA' },
  { id: 'meat', label: 'Meat', icon: '🥩', color: '#F87171' },
  { id: 'seafood', label: 'Seafood', icon: '🐟', color: '#93C5FD' },
  { id: 'grains', label: 'Grains', icon: '🌾', color: '#FBBF24' },
  { id: 'bakery', label: 'Bakery', icon: '🍞', color: '#D97706' },
  { id: 'beverages', label: 'Beverages', icon: '🥤', color: '#06B6D4' },
  { id: 'condiments', label: 'Condiments', icon: '🍯', color: '#F59E0B' },
  { id: 'oils', label: 'Oils & Vinegars', icon: '🫒', color: '#84CC16' },
  { id: 'baking', label: 'Baking', icon: '🧁', color: '#F472B6' },
  { id: 'spices', label: 'Spices', icon: '🌶️', color: '#EF4444' },
  { id: 'pasta', label: 'Pasta & Rice', icon: '🍝', color: '#A78BFA' },
  { id: 'canned', label: 'Canned Goods', icon: '🥫', color: '#FB923C' },
  { id: 'frozen', label: 'Frozen', icon: '🧊', color: '#67E8F9' },
  { id: 'snacks', label: 'Snacks', icon: '🍿', color: '#FACC15' },
  { id: 'other', label: 'Other', icon: '📦', color: '#9CA3AF' },
];

// Comprehensive ingredient to category mapping
const INGREDIENT_CATEGORY_MAP: { [key: string]: string } = {
  // Produce - Vegetables
  'onion': 'produce',
  'onions': 'produce',
  'garlic': 'produce',
  'garlics': 'produce',
  'tomato': 'produce',
  'tomatoes': 'produce',
  'potato': 'produce',
  'potatoes': 'produce',
  'carrot': 'produce',
  'carrots': 'produce',
  'celery': 'produce',
  'bell pepper': 'produce',
  'bell peppers': 'produce',
  'pepper': 'produce',
  'peppers': 'produce',
  'cucumber': 'produce',
  'cucumbers': 'produce',
  'lettuce': 'produce',
  'spinach': 'produce',
  'kale': 'produce',
  'broccoli': 'produce',
  'cauliflower': 'produce',
  'cabbage': 'produce',
  'zucchini': 'produce',
  'eggplant': 'produce',
  'mushroom': 'produce',
  'mushrooms': 'produce',
  'avocado': 'produce',
  'avocados': 'produce',
  'cilantro': 'produce',
  'parsley': 'produce',
  'basil': 'produce',
  'mint': 'produce',
  'dill': 'produce',
  'thyme': 'produce',
  'rosemary': 'produce',
  'sage': 'produce',
  'oregano': 'produce',
  'chives': 'produce',
  'scallion': 'produce',
  'scallions': 'produce',
  'green onion': 'produce',
  'green onions': 'produce',
  'leek': 'produce',
  'leeks': 'produce',
  'ginger': 'produce',
  'lemongrass': 'produce',
  'jalapeño': 'produce',
  'jalapeno': 'produce',
  'jalapeños': 'produce',
  'jalapenos': 'produce',
  'serrano': 'produce',
  'habanero': 'produce',
  'chipotle': 'produce',
  'poblano': 'produce',
  'corn': 'produce',
  'sweet corn': 'produce',
  'corn kernels': 'produce',
  'peas': 'produce',
  'green peas': 'produce',
  'snow peas': 'produce',
  'snap peas': 'produce',
  'lima beans': 'produce',
  'green beans': 'produce',
  'bean sprouts': 'produce',
  'sprouts': 'produce',
  'radish': 'produce',
  'radishes': 'produce',
  'turnip': 'produce',
  'turnips': 'produce',
  'beet': 'produce',
  'beets': 'produce',
  'sweet potato': 'produce',
  'sweet potatoes': 'produce',
  'yam': 'produce',
  'yams': 'produce',
  'squash': 'produce',
  'butternut squash': 'produce',
  'acorn squash': 'produce',
  'pumpkin': 'produce',
  'artichoke': 'produce',
  'artichokes': 'produce',
  'asparagus': 'produce',
  'brussels sprouts': 'produce',
  'okra': 'produce',
  'fennel': 'produce',
  'bok choy': 'produce',
  'napa cabbage': 'produce',
  'watercress': 'produce',
  'arugula': 'produce',
  'endive': 'produce',
  'radicchio': 'produce',
  'swiss chard': 'produce',
  'collard greens': 'produce',
  'turnip greens': 'produce',
  'mustard greens': 'produce',
  'dandelion greens': 'produce',

  // Produce - Fruits
  'apple': 'produce',
  'apples': 'produce',
  'banana': 'produce',
  'bananas': 'produce',
  'orange': 'produce',
  'oranges': 'produce',
  'lemon': 'produce',
  'lemons': 'produce',
  'lime': 'produce',
  'limes': 'produce',
  'grapefruit': 'produce',
  'grapefruits': 'produce',
  'strawberry': 'produce',
  'strawberries': 'produce',
  'blueberry': 'produce',
  'blueberries': 'produce',
  'raspberry': 'produce',
  'raspberries': 'produce',
  'blackberry': 'produce',
  'blackberries': 'produce',
  'grape': 'produce',
  'grapes': 'produce',
  'cherry': 'produce',
  'cherries': 'produce',
  'peach': 'produce',
  'peaches': 'produce',
  'pear': 'produce',
  'pears': 'produce',
  'plum': 'produce',
  'plums': 'produce',
  'apricot': 'produce',
  'apricots': 'produce',
  'mango': 'produce',
  'mangos': 'produce',
  'mangoes': 'produce',
  'pineapple': 'produce',
  'pineapples': 'produce',
  'kiwi': 'produce',
  'kiwis': 'produce',
  'papaya': 'produce',
  'papayas': 'produce',
  'cantaloupe': 'produce',
  'honeydew': 'produce',
  'watermelon': 'produce',
  'watermelons': 'produce',
  'melon': 'produce',
  'melons': 'produce',
  'coconut': 'produce',
  'coconuts': 'produce',
  'cranberry': 'produce',
  'cranberries': 'produce',
  'pomegranate': 'produce',
  'pomegranates': 'produce',
  'fig': 'produce',
  'figs': 'produce',
  'date': 'produce',
  'dates': 'produce',
  'raisin': 'produce',
  'raisins': 'produce',
  'prune': 'produce',
  'prunes': 'produce',

  // Dairy
  'milk': 'dairy',
  'whole milk': 'dairy',
  'skim milk': 'dairy',
  '2% milk': 'dairy',
  'low-fat milk': 'dairy',
  'almond milk': 'beverages',
  'soy milk': 'beverages',
  'oat milk': 'beverages',
  'coconut milk': 'beverages',
  'cream': 'dairy',
  'heavy cream': 'dairy',
  'heavy whipping cream': 'dairy',
  'whipping cream': 'dairy',
  'light cream': 'dairy',
  'half and half': 'dairy',
  'sour cream': 'dairy',
  'crème fraîche': 'dairy',
  'creme fraiche': 'dairy',
  'butter': 'dairy',
  'unsalted butter': 'dairy',
  'salted butter': 'dairy',
  'margarine': 'dairy',
  'cheese': 'dairy',
  'cheddar cheese': 'dairy',
  'mozzarella cheese': 'dairy',
  'parmesan cheese': 'dairy',
  'swiss cheese': 'dairy',
  'goat cheese': 'dairy',
  'feta cheese': 'dairy',
  'blue cheese': 'dairy',
  'brie cheese': 'dairy',
  'camembert cheese': 'dairy',
  'ricotta cheese': 'dairy',
  'cottage cheese': 'dairy',
  'cream cheese': 'dairy',
  'mascarpone': 'dairy',
  'yogurt': 'dairy',
  'greek yogurt': 'dairy',
  'plain yogurt': 'dairy',
  'vanilla yogurt': 'dairy',
  'ice cream': 'dairy',
  'frozen yogurt': 'frozen',
  'egg': 'dairy',
  'eggs': 'dairy',
  'egg white': 'dairy',
  'egg whites': 'dairy',
  'egg yolk': 'dairy',
  'egg yolks': 'dairy',

  // Meat
  'chicken': 'meat',
  'chicken breast': 'meat',
  'chicken breasts': 'meat',
  'chicken thigh': 'meat',
  'chicken thighs': 'meat',
  'chicken leg': 'meat',
  'chicken legs': 'meat',
  'chicken wing': 'meat',
  'chicken wings': 'meat',
  'chicken drumstick': 'meat',
  'chicken drumsticks': 'meat',
  'ground chicken': 'meat',
  'beef': 'meat',
  'ground beef': 'meat',
  'steak': 'meat',
  'steaks': 'meat',
  'beef chuck': 'meat',
  'beef brisket': 'meat',
  'beef short ribs': 'meat',
  'beef sirloin': 'meat',
  'beef tenderloin': 'meat',
  'filet mignon': 'meat',
  'ribeye': 'meat',
  'new york strip': 'meat',
  't-bone': 'meat',
  'porterhouse': 'meat',
  'pork': 'meat',
  'pork chop': 'meat',
  'pork chops': 'meat',
  'pork shoulder': 'meat',
  'pork loin': 'meat',
  'pork tenderloin': 'meat',
  'ground pork': 'meat',
  'bacon': 'meat',
  'ham': 'meat',
  'prosciutto': 'meat',
  'sausage': 'meat',
  'italian sausage': 'meat',
  'bratwurst': 'meat',
  'chorizo': 'meat',
  'pepperoni': 'meat',
  'salami': 'meat',
  'turkey': 'meat',
  'ground turkey': 'meat',
  'turkey breast': 'meat',
  'turkey thigh': 'meat',
  'lamb': 'meat',
  'ground lamb': 'meat',
  'lamb chop': 'meat',
  'lamb chops': 'meat',
  'leg of lamb': 'meat',
  'lamb shank': 'meat',
  'veal': 'meat',
  'duck': 'meat',
  'goose': 'meat',
  'venison': 'meat',
  'rabbit': 'meat',

  // Seafood
  'fish': 'seafood',
  'salmon': 'seafood',
  'salmon fillet': 'seafood',
  'salmon fillets': 'seafood',
  'tuna': 'seafood',
  'tuna steak': 'seafood',
  'cod': 'seafood',
  'halibut': 'seafood',
  'mahi mahi': 'seafood',
  'tilapia': 'seafood',
  'snapper': 'seafood',
  'sea bass': 'seafood',
  'flounder': 'seafood',
  'sole': 'seafood',
  'mackerel': 'seafood',
  'sardines': 'seafood',
  'anchovies': 'seafood',
  'trout': 'seafood',
  'catfish': 'seafood',
  'pike': 'seafood',
  'walleye': 'seafood',
  'perch': 'seafood',
  'shrimp': 'seafood',
  'prawns': 'seafood',
  'crab': 'seafood',
  'crab meat': 'seafood',
  'lobster': 'seafood',
  'lobster tail': 'seafood',
  'scallops': 'seafood',
  'mussels': 'seafood',
  'clams': 'seafood',
  'oysters': 'seafood',
  'squid': 'seafood',
  'calamari': 'seafood',
  'octopus': 'seafood',

  // Grains
  'rice': 'grains',
  'white rice': 'grains',
  'brown rice': 'grains',
  'jasmine rice': 'grains',
  'basmati rice': 'grains',
  'wild rice': 'grains',
  'arborio rice': 'grains',
  'quinoa': 'grains',
  'barley': 'grains',
  'oats': 'grains',
  'rolled oats': 'grains',
  'steel cut oats': 'grains',
  'wheat': 'grains',
  'wheat berries': 'grains',
  'bulgur': 'grains',
  'farro': 'grains',
  'spelt': 'grains',
  'rye': 'grains',
  'millet': 'grains',
  'buckwheat': 'grains',
  'amaranth': 'grains',
  'couscous': 'grains',
  'cornmeal': 'grains',
  'polenta': 'grains',
  'hominy': 'grains',

  // Pasta & Rice (separate from grains for better categorization)
  'pasta': 'pasta',
  'spaghetti': 'pasta',
  'linguine': 'pasta',
  'fettuccine': 'pasta',
  'penne': 'pasta',
  'rigatoni': 'pasta',
  'fusilli': 'pasta',
  'rotini': 'pasta',
  'farfalle': 'pasta',
  'bow tie pasta': 'pasta',
  'macaroni': 'pasta',
  'elbow macaroni': 'pasta',
  'shells': 'pasta',
  'conchiglie': 'pasta',
  'ravioli': 'pasta',
  'tortellini': 'pasta',
  'gnocchi': 'pasta',
  'lasagna sheets': 'pasta',
  'lasagna noodles': 'pasta',
  'angel hair': 'pasta',
  'capellini': 'pasta',
  'orzo': 'pasta',
  'ditalini': 'pasta',
  'cavatappi': 'pasta',
  'gemelli': 'pasta',
  'orecchiette': 'pasta',
  'pappardelle': 'pasta',
  'tagliatelle': 'pasta',
  'ramen noodles': 'pasta',
  'udon noodles': 'pasta',
  'soba noodles': 'pasta',
  'rice noodles': 'pasta',
  'vermicelli': 'pasta',

  // Bakery
  'bread': 'bakery',
  'white bread': 'bakery',
  'whole wheat bread': 'bakery',
  'sourdough bread': 'bakery',
  'rye bread': 'bakery',
  'pumpernickel bread': 'bakery',
  'baguette': 'bakery',
  'ciabatta': 'bakery',
  'focaccia': 'bakery',
  'pita bread': 'bakery',
  'naan': 'bakery',
  'tortilla': 'bakery',
  'flour tortilla': 'bakery',
  'corn tortilla': 'bakery',
  'bagel': 'bakery',
  'bagels': 'bakery',
  'english muffin': 'bakery',
  'english muffins': 'bakery',
  'croissant': 'bakery',
  'croissants': 'bakery',
  'danish': 'bakery',
  'muffin': 'bakery',
  'muffins': 'bakery',
  'scone': 'bakery',
  'scones': 'bakery',
  'biscuit': 'bakery',
  'biscuits': 'bakery',
  'roll': 'bakery',
  'rolls': 'bakery',
  'dinner roll': 'bakery',
  'dinner rolls': 'bakery',
  'hamburger bun': 'bakery',
  'hamburger buns': 'bakery',
  'hot dog bun': 'bakery',
  'hot dog buns': 'bakery',
  'brioche': 'bakery',
  'challah': 'bakery',
  'pretzel': 'bakery',
  'pretzels': 'bakery',

  // Beverages
  'water': 'beverages',
  'sparkling water': 'beverages',
  'soda': 'beverages',
  'cola': 'beverages',
  'juice': 'beverages',
  'apple juice': 'beverages',
  'orange juice': 'beverages',
  'cranberry juice': 'beverages',
  'grape juice': 'beverages',
  'lemon juice': 'beverages',
  'lime juice': 'beverages',
  'tomato juice': 'beverages',
  'vegetable juice': 'beverages',
  'coffee': 'beverages',
  'tea': 'beverages',
  'green tea': 'beverages',
  'black tea': 'beverages',
  'herbal tea': 'beverages',
  'chamomile tea': 'beverages',
  'beer': 'beverages',
  'wine': 'beverages',
  'red wine': 'beverages',
  'white wine': 'beverages',
  'champagne': 'beverages',
  'vodka': 'beverages',
  'rum': 'beverages',
  'whiskey': 'beverages',
  'gin': 'beverages',
  'tequila': 'beverages',
  'brandy': 'beverages',
  'coconut water': 'beverages',
  'energy drink': 'beverages',
  'sports drink': 'beverages',

  // Condiments & Sauces
  'ketchup': 'condiments',
  'mustard': 'condiments',
  'mayonnaise': 'condiments',
  'mayo': 'condiments',
  'relish': 'condiments',
  'pickle': 'condiments',
  'pickles': 'condiments',
  'hot sauce': 'condiments',
  'tabasco': 'condiments',
  'sriracha': 'condiments',
  'worcestershire sauce': 'condiments',
  'soy sauce': 'condiments',
  'tamari': 'condiments',
  'teriyaki sauce': 'condiments',
  'hoisin sauce': 'condiments',
  'oyster sauce': 'condiments',
  'fish sauce': 'condiments',
  'barbecue sauce': 'condiments',
  'bbq sauce': 'condiments',
  'steak sauce': 'condiments',
  'salsa': 'condiments',
  'marinara sauce': 'condiments',
  'tomato sauce': 'condiments',
  'pasta sauce': 'condiments',
  'alfredo sauce': 'condiments',
  'pesto': 'condiments',
  'ranch dressing': 'condiments',
  'italian dressing': 'condiments',
  'caesar dressing': 'condiments',
  'vinaigrette': 'condiments',
  'honey': 'condiments',
  'maple syrup': 'condiments',
  'agave nectar': 'condiments',
  'molasses': 'condiments',
  'jam': 'condiments',
  'jelly': 'condiments',
  'marmalade': 'condiments',
  'peanut butter': 'condiments',
  'almond butter': 'condiments',
  'nutella': 'condiments',
  'tahini': 'condiments',
  'hummus': 'condiments',

  // Oils & Vinegars
  'olive oil': 'oils',
  'extra virgin olive oil': 'oils',
  'vegetable oil': 'oils',
  'canola oil': 'oils',
  'sunflower oil': 'oils',
  'safflower oil': 'oils',
  'avocado oil': 'oils',
  'coconut oil': 'oils',
  'sesame oil': 'oils',
  'peanut oil': 'oils',
  'grapeseed oil': 'oils',
  'corn oil': 'oils',
  'soybean oil': 'oils',
  'palm oil': 'oils',
  'lard': 'oils',
  'shortening': 'oils',
  'cooking spray': 'oils',
  'vinegar': 'oils',
  'white vinegar': 'oils',
  'apple cider vinegar': 'oils',
  'balsamic vinegar': 'oils',
  'red wine vinegar': 'oils',
  'white wine vinegar': 'oils',
  'rice vinegar': 'oils',
  'sherry vinegar': 'oils',
  'champagne vinegar': 'oils',
  'malt vinegar': 'oils',

  // Spices & Seasonings
  'salt': 'spices',
  'black pepper': 'spices',
  'white pepper': 'spices',
  'red pepper flakes': 'spices',
  'cayenne pepper': 'spices',
  'paprika': 'spices',
  'chili powder': 'spices',
  'cumin': 'spices',
  'coriander': 'spices',
  'turmeric': 'spices',
  'cinnamon': 'spices',
  'nutmeg': 'spices',
  'cloves': 'spices',
  'allspice': 'spices',
  'cardamom': 'spices',
  'bay leaves': 'spices',
  'bay leaf': 'spices',
  'dried thyme': 'spices',
  'dried oregano': 'spices',
  'dried basil': 'spices',
  'dried parsley': 'spices',
  'dried dill': 'spices',
  'dried rosemary': 'spices',
  'dried sage': 'spices',
  'onion powder': 'spices',
  'garlic powder': 'spices',
  'ginger powder': 'spices',
  'mustard seed': 'spices',
  'celery seed': 'spices',
  'fennel seed': 'spices',
  'caraway seed': 'spices',
  'sesame seeds': 'spices',
  'poppy seeds': 'spices',
  'vanilla extract': 'spices',
  'almond extract': 'spices',
  'lemon extract': 'spices',
  'peppermint extract': 'spices',
  'curry powder': 'spices',
  'garam masala': 'spices',
  'five spice': 'spices',
  'herbs de provence': 'spices',
  'italian seasoning': 'spices',
  'taco seasoning': 'spices',
  'cajun seasoning': 'spices',
  'old bay': 'spices',
  'ranch seasoning': 'spices',

  // Baking
  'flour': 'baking',
  'all-purpose flour': 'baking',
  'bread flour': 'baking',
  'cake flour': 'baking',
  'pastry flour': 'baking',
  'whole wheat flour': 'baking',
  'almond flour': 'baking',
  'coconut flour': 'baking',
  'rice flour': 'baking',
  'cornstarch': 'baking',
  'arrowroot': 'baking',
  'tapioca starch': 'baking',
  'potato starch': 'baking',
  'baking powder': 'baking',
  'baking soda': 'baking',
  'yeast': 'baking',
  'active dry yeast': 'baking',
  'instant yeast': 'baking',
  'sugar': 'baking',
  'white sugar': 'baking',
  'granulated sugar': 'baking',
  'brown sugar': 'baking',
  'light brown sugar': 'baking',
  'dark brown sugar': 'baking',
  'powdered sugar': 'baking',
  'confectioners sugar': 'baking',
  'coconut sugar': 'baking',
  'raw sugar': 'baking',
  'turbinado sugar': 'baking',
  'demerara sugar': 'baking',
  'muscovado sugar': 'baking',
  'palm sugar': 'baking',
  'stevia': 'baking',
  'artificial sweetener': 'baking',
  'cocoa powder': 'baking',
  'unsweetened cocoa': 'baking',
  'dutch process cocoa': 'baking',
  'chocolate chips': 'baking',
  'dark chocolate': 'baking',
  'milk chocolate': 'baking',
  'white chocolate': 'baking',
  'baking chocolate': 'baking',
  'unsweetened chocolate': 'baking',
  'semi-sweet chocolate': 'baking',

  // Canned Goods
  'canned tomatoes': 'canned',
  'diced tomatoes': 'canned',
  'crushed tomatoes': 'canned',
  'tomato paste': 'canned',
  'tomato puree': 'canned',
  'canned beans': 'canned',
  'black beans': 'canned',
  'kidney beans': 'canned',
  'pinto beans': 'canned',
  'navy beans': 'canned',
  'great northern beans': 'canned',
  'lima beans': 'canned',
  'garbanzo beans': 'canned',
  'chickpeas': 'canned',
  'cannellini beans': 'canned',
  'lentils': 'canned',
  'split peas': 'canned',
  'canned corn': 'canned',
  'canned peas': 'canned',
  'canned carrots': 'canned',
  'canned green beans': 'canned',
  'canned mushrooms': 'canned',
  'canned olives': 'canned',
  'black olives': 'canned',
  'green olives': 'canned',
  'kalamata olives': 'canned',
  'canned peppers': 'canned',
  'roasted red peppers': 'canned',
  'canned chilies': 'canned',
  'diced green chilies': 'canned',
  'canned pumpkin': 'canned',
  'pumpkin puree': 'canned',
  'canned coconut milk': 'canned',
  'coconut cream': 'canned',
  'canned broth': 'canned',
  'chicken broth': 'canned',
  'beef broth': 'canned',
  'vegetable broth': 'canned',
  'chicken stock': 'canned',
  'beef stock': 'canned',
  'vegetable stock': 'canned',
  'canned soup': 'canned',

  // Frozen
  'frozen vegetables': 'frozen',
  'frozen peas': 'frozen',
  'frozen corn': 'frozen',
  'frozen broccoli': 'frozen',
  'frozen spinach': 'frozen',
  'frozen carrots': 'frozen',
  'frozen green beans': 'frozen',
  'frozen mixed vegetables': 'frozen',
  'frozen berries': 'frozen',
  'frozen strawberries': 'frozen',
  'frozen blueberries': 'frozen',
  'frozen raspberries': 'frozen',
  'frozen blackberries': 'frozen',
  'frozen mango': 'frozen',
  'frozen pineapple': 'frozen',
  'frozen peaches': 'frozen',
  'frozen cherries': 'frozen',
  'frozen edamame': 'frozen',
  'frozen pizza': 'frozen',
  'frozen waffles': 'frozen',
  'frozen pancakes': 'frozen',
  'frozen french fries': 'frozen',
  'frozen hash browns': 'frozen',
  'frozen tater tots': 'frozen',
  'frozen fish sticks': 'frozen',
  'frozen chicken nuggets': 'frozen',
  'frozen burgers': 'frozen',
  'frozen meatballs': 'frozen',

  // Snacks
  'chips': 'snacks',
  'potato chips': 'snacks',
  'tortilla chips': 'snacks',
  'corn chips': 'snacks',
  'crackers': 'snacks',
  'pretzels': 'snacks',
  'popcorn': 'snacks',
  'nuts': 'snacks',
  'peanuts': 'snacks',
  'almonds': 'snacks',
  'walnuts': 'snacks',
  'pecans': 'snacks',
  'cashews': 'snacks',
  'pistachios': 'snacks',
  'macadamia nuts': 'snacks',
  'brazil nuts': 'snacks',
  'hazelnuts': 'snacks',
  'pine nuts': 'snacks',
  'sunflower seeds': 'snacks',
  'pumpkin seeds': 'snacks',
  'mixed nuts': 'snacks',
  'trail mix': 'snacks',
  'granola': 'snacks',
  'granola bars': 'snacks',
  'energy bars': 'snacks',
  'protein bars': 'snacks',
  'cookies': 'snacks',
  'candy': 'snacks',
  'chocolate': 'snacks',
  'gummy bears': 'snacks',
  'mints': 'snacks',
  'gum': 'snacks',
};

/**
 * Get the appropriate food category for an ingredient name
 */
export function getIngredientCategory(ingredientName: string): FoodCategory {
  const normalizedName = ingredientName.toLowerCase().trim();
  
  // Direct match
  const categoryId = INGREDIENT_CATEGORY_MAP[normalizedName];
  if (categoryId) {
    const category = FOOD_CATEGORIES.find(cat => cat.id === categoryId);
    if (category) return category;
  }
  
  // Partial match - check if the ingredient name contains any known ingredients
  for (const [knownIngredient, categoryId] of Object.entries(INGREDIENT_CATEGORY_MAP)) {
    if (normalizedName.includes(knownIngredient) || knownIngredient.includes(normalizedName)) {
      const category = FOOD_CATEGORIES.find(cat => cat.id === categoryId);
      if (category) return category;
    }
  }
  
  // Default to 'other' category
  return FOOD_CATEGORIES.find(cat => cat.id === 'other') || FOOD_CATEGORIES[FOOD_CATEGORIES.length - 1];
}

/**
 * Get the icon for an ingredient
 */
export function getIngredientIcon(ingredientName: string): string {
  const category = getIngredientCategory(ingredientName);
  return category.icon;
}

/**
 * Get the color for an ingredient category
 */
export function getIngredientColor(ingredientName: string): string {
  const category = getIngredientCategory(ingredientName);
  return category.color;
}

/**
 * Capitalize the first letter of each word in a string
 * Handles special cases like "al dente", "à la", etc.
 */
export function capitalizeIngredientName(name: string): string {
  if (!name) return '';
  
  // Special cases that shouldn't be capitalized
  const lowercaseWords = ['a', 'an', 'and', 'as', 'at', 'but', 'by', 'for', 'if', 'in', 'of', 'on', 'or', 'the', 'to', 'up', 'via', 'with'];
  const specialCases = ['al dente', 'à la', 'au jus', 'sous vide', 'en papillote'];
  
  // Check for special cases first
  const lowerName = name.toLowerCase().trim();
  for (const specialCase of specialCases) {
    if (lowerName.includes(specialCase)) {
      return name.replace(new RegExp(specialCase, 'gi'), specialCase);
    }
  }
  
  return name
    .toLowerCase()
    .split(/[\s-]+/)
    .map((word, index) => {
      // Always capitalize first word
      if (index === 0) {
        return word.charAt(0).toUpperCase() + word.slice(1);
      }
      
      // Don't capitalize common lowercase words unless they're the first word
      if (lowercaseWords.includes(word)) {
        return word;
      }
      
      // Capitalize other words
      return word.charAt(0).toUpperCase() + word.slice(1);
    })
    .join(' ');
}