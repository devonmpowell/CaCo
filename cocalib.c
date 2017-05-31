// blackjack.c
// functions for computing optimal plays in blackjack

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

// define useful stuff
#define STAND 0
#define HIT 1
#define DOUBLE 2
#define SPLIT 3
#define SURRENDER 4
#define INSURANCE 5
typedef double real;
typedef struct {
	int points;
	int softness;
	int numcards;
	int depth;
	int ispair;
} Hand;
typedef struct {
	int num[12]; // only indices 2-11 are used
	int total;
	int numdecks; 
} Shoe;
typedef struct {
	int allowed[6]; // only indices 2-11 are used
	int max_split_depth;
	int double_after_split;
	int dealer_hits_soft_17;
	int can_hit_split_aces;
	real errtol;
} Rules;
typedef struct {
	int actions[10][34]; 
	int optimal; 
} Strategy; 

// prototypes
void seed_rand(int seed);
void init_shoe(Shoe* shoe, int numdecks);
void init_hand(Hand* hand);
int blackjack(Hand hand);
int split_to_21(Hand hand);
real choose_card_from_shoe(Shoe* shoe, int card);
void add_card_to_hand(Hand* hand, int card);
int deal_card_to_hand_random(Shoe* shoe, Hand* hand);
real deal_card_to_hand_choose(Shoe* shoe, Hand* hand, int card);
void exp_stand(real bet, Hand hand, Hand dealer, Shoe shoe, Rules rules, real* exp);
void expected_value(real bet, Hand hand, Hand dealer, Shoe shoe, Rules rules, Strategy strategy, int* best_action, real* all_exp);
void chart_ind_from_hands(Hand hand, Hand dealer, int* my_ind, int* dealer_ind); 
void simulate_unit_bet(Hand hand, Hand dealer, Shoe shoe, Rules rules, Strategy strategy, int* best_action, real* all_exp);

// the main function
void simulate_unit_bet(Hand hand, Hand dealer, Shoe shoe, Rules rules, Strategy strategy, int* best_action, real* all_exp) {

	// simulate on the whole unit bet
	// NOTE: assumes that all allowed moves have been passed correctly!
	expected_value(1.0, hand, dealer, shoe, rules, strategy, best_action, all_exp);
}

// returns the expected value for the best possible action for the given hand
void expected_value(real bet, Hand hand, Hand dealer, Shoe shoe, Rules rules, Strategy strategy, int* best_action, real* all_exp) {


	// from WIZARD of ODDS:
	// following rules: dealer stands on a soft 17, an infinite deck, the player may double
	// after a split, split up to three times except for aces, and draw only one card to split
	// aces. Based on these rules, the player's expected value is -0.511734%.'

	int c, c0, c1, a, batmp, dealer_ind, my_ind;
	real max_exp, prb, prc0, prc1, exptmp[6];
	Hand ht0, ht1, htmp;
	Shoe st0, st1, stmp;
	Rules rtmp;

	// return if the bet is << 1
	if(bet < rules.errtol) {
		*best_action = STAND;
		all_exp[STAND] = 0.0;
		return;
	} 

	// simulate the expected value of standing
	// should always be allowed 
	if(rules.allowed[STAND]) {

		// guard against soft hands exceeding 21
		htmp = hand;
		while(htmp.softness > 0 && htmp.points > 21) {
			htmp.points -= 10;
			htmp.softness -= 1;
		}

		// get the expected value of standing on this hand
		exp_stand(bet, htmp, dealer, shoe, rules, &all_exp[STAND]);
	}

	// simulate the expected value of hitting 
	if(rules.allowed[HIT]) { // should be always

		// hitting precludes anything but hit or stand afterwards
		rtmp = rules;
		rtmp.allowed[SPLIT] = 0; 
		rtmp.allowed[DOUBLE] = 0;
		rtmp.allowed[SURRENDER] = 0;
		rtmp.allowed[INSURANCE] = 0;

		// recursively sum the expected gain from each possible draw
		all_exp[HIT] = 0.0;
		for(c = 2; c <= 11; ++c) {
			htmp = hand;
			stmp = shoe;
			if(stmp.num[c] <= 0) continue;
	
			// bust or recurse, weighting sub-expected values
			// by the probability that c is drawn
			prb = deal_card_to_hand_choose(&stmp, &htmp, c); 
			if(htmp.points > 21) {
				all_exp[HIT] -= prb*bet;	
			} 
			else  {
				expected_value(prb*bet, htmp, dealer, stmp, rtmp, strategy, &batmp, exptmp);
				all_exp[HIT] += exptmp[batmp]; // use the action giving the highest expected outcome
			}
		}
	}

	// simulate the expected value of doubling (allowed exactly one more card) 
	if(rules.allowed[DOUBLE]) { 
		all_exp[DOUBLE] = 0.0;
		for(c = 2; c <= 11; ++c) {
			htmp = hand;
			stmp = shoe;
			if(stmp.num[c] <= 0) continue;
	
			// get the expected value of standing on twice the original bet 
			prb = deal_card_to_hand_choose(&stmp, &htmp, c); 
			if(htmp.points > 21) {
				all_exp[DOUBLE] -= prb*2.0*bet;	
			} 
			else {
				exp_stand(2.0*prb*bet, htmp, dealer, stmp, rules, exptmp);
				all_exp[DOUBLE] += exptmp[0];
			} 
		}
	}

	// simulate splitting, if hand is a pair and splitting is allowed
	// can only split up to a maximum depth 
	rules.allowed[SPLIT] *= hand.ispair;
	rules.allowed[SPLIT] *= (hand.depth < (2+rules.max_split_depth)); 
	if(rules.allowed[SPLIT]) {

		// Make the split hand
		// Do not decrement the hand depth though!
		htmp = hand; 
		htmp.points /= 2; 
		htmp.softness /= 2; 
		htmp.numcards /= 2;
		htmp.ispair = 0; 

		// set up post-split rules
		all_exp[SPLIT] = 0.0;
		rtmp = rules;
		if(htmp.points == 11 && !rtmp.can_hit_split_aces) {

			// if the player splits aces, we can only take one more card
			// unless splitting again, up to the max depth
			rtmp.allowed[HIT] = 0; 
			rtmp.allowed[DOUBLE] = 0;
		}
		else {

			// player may double or hit after split, depending on the rules 
			rtmp.allowed[DOUBLE] *= (rtmp.double_after_split > 0); 
		}

		// we must simulate all possible combinations of the next two cards
		// to precisely capture the state of the deck after two subsequent draws 
		for(c0 = 2; c0 <= 11; ++c0) {
			st0 = shoe;
			ht0 = htmp;
			prc0 = deal_card_to_hand_choose(&st0, &ht0, c0); 
			for(c1 = 2; c1 <= 11; ++c1) {
				st1 = st0;
				ht1 = htmp;
				prc1 = deal_card_to_hand_choose(&st1, &ht1, c1); 

				// play out the two sub-hand independently
				expected_value(prc0*prc1*bet, ht0, dealer, st0, rtmp, strategy, &batmp, exptmp);
				all_exp[SPLIT] += exptmp[batmp];
				expected_value(prc0*prc1*bet, ht1, dealer, st1, rtmp, strategy, &batmp, exptmp);
				all_exp[SPLIT] += exptmp[batmp];
			}
		}
	}

	// if these two hands are freshly dealt, 
	// do pre-play options and side bets
	rules.allowed[SURRENDER] *= (hand.depth <= 2);
	if(dealer.depth == 1 && hand.depth == 2) {
		// surrender forfiets half the bet.
		// See if this beats anything
		if(rules.allowed[SURRENDER])
			all_exp[SURRENDER] = -0.5*bet;
	}


	// Decide which action yields the greatest expected value,
	// given the current knowledge of the deck and visible cards
	for(a = 0; a < 6; ++a)
		if(!rules.allowed[a])
			all_exp[a] = -1000*bet;
	if(strategy.optimal) {
		max_exp = -1000*bet;
		for(a = 0; a < 6; ++a) {
			if(all_exp[a] > max_exp) {
				*best_action = a;
				max_exp = all_exp[a];
			}
		}
	}
	else {
		if(hand.points > 19 && !hand.softness) {
			*best_action = STAND;
		}
		else {
			chart_ind_from_hands(hand, dealer, &my_ind, &dealer_ind);
			*best_action = strategy.actions[dealer_ind][my_ind];
			while(!rules.allowed[*best_action]) {

				// seconday options from the strategy chart
				if(*best_action == SURRENDER) {
					if(hand.points >= 17)
						*best_action = STAND;
					else
						*best_action = HIT;
				}
				else if(*best_action == DOUBLE)
					*best_action = HIT;
				else if(*best_action == SPLIT)
					*best_action = HIT;
				else if(*best_action == HIT)
					*best_action = STAND;
			}

			//if(!rules.allowed[*best_action]) {
				//printf("STOP! action = %d, rules = %d %d %d %d %d %d \n", *best_action,
						//rules.allowed[0], rules.allowed[1], rules.allowed[2], rules.allowed[3], rules.allowed[4], rules.allowed[5]);
				//exit(0);
			//}
		}
	}
}


// gives the expected winnings if the player stands
void exp_stand(real bet, Hand hand, Hand dealer, Shoe shoe, Rules rules, real* exp) {

	int c;
	real prb, exptmp;
	Hand dtmp;
	Shoe stmp;

	// stop if bet << 1
	*exp = 0.0;
	if(bet < rules.errtol) 
		return;

	// dealer hits
	if(dealer.points < 17
			|| (rules.dealer_hits_soft_17 && dealer.points == 17 && dealer.softness)) {

		// simulate the dealers hit/stand/bust, recursing as needed
		for(c = 2; c <= 11; ++c) {
			dtmp = dealer;
			stmp = shoe;
			if(stmp.num[c] <= 0) continue;

			prb = deal_card_to_hand_choose(&stmp, &dtmp, c); 

			// got through special win/loss scenarios 
			// barring all else, try hitting again
			// split to 21 beats a non-blackjack dealer 21
			// in all cases, push against dealer 21
			if(blackjack(dtmp)) {
				if(!blackjack(hand) && !split_to_21(hand))
					*exp -= 1.0*prb*bet;
			}
			else if(blackjack(hand)) {
				*exp += 1.5*prb*bet;
			}
			else if(split_to_21(hand)) {
				*exp += 1.0*prb*bet;
			}
			else if(dtmp.points > 21) {
				*exp += 1.0*prb*bet;	
			} 
			else {
				exp_stand(prb*bet, hand, dtmp, stmp, rules, &exptmp); 
				*exp += exptmp;
			}
		}
	}

	// the dealer must stand. See who won.
	else {
		if(dealer.points < hand.points) 
			*exp = +1.0*bet;
		if(dealer.points > hand.points)
			*exp = -1.0*bet;
	}
}



// helper functions to operate on Shoes and Hands
// i.e. multinomial probabilites and random choices

void init_shoe(Shoe* shoe, int numdecks) {
	int c;
	memset(shoe, 0, sizeof(Shoe));
	if(numdecks < 0) {
		shoe->numdecks = -1; 
		numdecks = 1;
	}
	else {
		shoe->numdecks = numdecks;
	}
	for(c = 2; c <= 9; ++c) {
		shoe->num[c] += 4*numdecks;
		shoe->total += 4*numdecks;
	}
	shoe->num[10] += 16*numdecks;
	shoe->total += 16*numdecks;
	shoe->num[11] += 4*numdecks;
	shoe->total += 4*numdecks;
}

void init_hand(Hand* hand) {
	memset(hand, 0, sizeof(Hand));
}

real choose_card_from_shoe(Shoe* shoe, int card) {

	real prb;
	if(!shoe->num[card]) 
		return 0.0;
	
	// decrements the deck state
	// returns the probability of this draw BEFORE decrementing the deck!
	// shoe->numdecks < 0 means infinite deck
	prb = ((real)shoe->num[card])/shoe->total;
	if(shoe->numdecks >= 0) { 
		shoe->num[card] -= 1;
		shoe->total -= 1;
	}

	return prb;
}

int random_card_from_shoe(Shoe* shoe) {

	int card;	
	real cdf, x;
	if(!shoe->total) 
		return 0;

	// multinomial distribution
	// TODO: untested!
	x = (1.0*rand())/RAND_MAX; 
	card = 2;
	cdf = ((real)shoe->num[card])/shoe->total;
	while(x > cdf) {
		card += 1;
		cdf += ((real)shoe->num[card])/shoe->total;
	}
	
	// decrements the deck state, 
	// shoe->numdecks < 0 means infinite deck
	if(shoe->numdecks >= 0) { 
		shoe->num[card] -= 1;
		shoe->total -= 1;
	}

	return card;
}


void add_card_to_hand(Hand* hand, int card) {

	// first see if we have a pair 
	if(hand->numcards == 1 && card == hand->points)
		hand->ispair = 1;
	else
		hand->ispair = 0;

	// update the hand
	hand->points += card;
	hand->softness += (card == 11);
	hand->numcards += 1;
	hand->depth += 1;

	// if we have a soft hand, avoid busting
	while(!hand->ispair && hand->softness > 0 && hand->points > 21) {
		hand->points -= 10;
		hand->softness -= 1;
	}
}

int deal_card_to_hand_random(Shoe* shoe, Hand* hand) {
	int card;
	card = random_card_from_shoe(shoe);
	add_card_to_hand(hand, card);
	return card;
}

real deal_card_to_hand_choose(Shoe* shoe, Hand* hand, int card) {
	real prb;
	prb = choose_card_from_shoe(shoe, card);
	if(prb > 0.0) add_card_to_hand(hand, card);
	return prb;
}

void chart_ind_from_hands(Hand hand, Hand dealer, int* my_ind, int* dealer_ind) {

	if(hand.ispair) 
		*my_ind = 35 - (hand.points/2); 
	else if(hand.softness)
		*my_ind = 36 - hand.points;
	else 
		*my_ind = 19 - hand.points;

	*dealer_ind = (dealer.points-2);
}


// seeeds the random number generator
void seed_rand(int seed) {
	srand(seed);
}

// checks for player blackjack
int blackjack(Hand hand) {
	return (hand.depth == 2 && hand.numcards == 2 && hand.points == 21);
}

// checks for player 21 with two cards off of a split 
int split_to_21(Hand hand) {
	return (hand.depth > 2 && hand.numcards == 2 && hand.points == 21);
}
