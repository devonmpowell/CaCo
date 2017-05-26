// blackjack.c
// functions for computing optimal plays in blackjack

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

// define useful stuff
#define ERRTOL 1.0e-5
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
	int ispair;
} Hand;
typedef struct {
	int num[12]; // only indices 2-11 are used
	int total;
	int numdecks; 
} Shoe;

// prototypes
void init_shoe(Shoe* shoe, int numdecks);
void init_hand(Hand* hand);
real choose_card_from_shoe(Shoe* shoe, int card);
void add_card_to_hand(Hand* hand, int card);
int deal_card_to_hand_random(Shoe* shoe, Hand* hand);
real deal_card_to_hand_choose(Shoe* shoe, Hand* hand, int card);
void exp_stand(real bet, Hand hand, Hand dealer, Shoe shoe, real* exp);
void expected_value(real bet, Hand hand, Hand dealer, Shoe shoe, int* allowed, int* best_action, real* all_exp, int depth);
void chart_ind_from_hands(Hand hand, Hand dealer, int* my_ind, int* dealer_ind); 

// the main function
// returns the expected value for the best possible action for the given hand
void expected_value(real bet, Hand hand, Hand dealer, Shoe shoe, int* allowed, int* best_action, real* all_exp, int depth) {

	int c, c0, c1, a, batmp, acttmp[6];
	real max_exp, prb, prc0, prc1, exptmp[6];
	Hand ht0, ht1, htmp;
	Shoe st0, st1, stmp;

	// return if the bet is << 1
	if(bet < ERRTOL) {
		*best_action = STAND;
		all_exp[STAND] = 0.0;
		return;
	} 

	// if we have just dealt the hand, check for dealer/player blackjack
	if(!depth) {
	
		// probability of dealer blackjack
		//prb = 0.0;
		//if(dealer.points == 10) {
			//prb = ((real)shoe.num[11])/shoe.total;
			
		//}
		//else if(dealer.points == 11) {
			//prb = ((real)shoe.num[10])/shoe.total;
		//}

		// if we have a blackjack, 
		if(hand.points == 21) {
			//printf("bj, bet = %f\n", bet);
			*best_action = STAND;
			all_exp[STAND] = 1.5*bet;//*(1.0-prb);
			return;
		}
		else {
			// probability of losing to dealer BJ, or push
		}
	
	
	
	
	}

	// simulate the expected value of standing
	// should always be allowed 
	if(allowed[STAND]) {

		// guard against soft hands exceeding 21
		htmp = hand;
		while(htmp.softness > 0 && htmp.points > 21) {
			htmp.points -= 10;
			htmp.softness -= 1;
		}

		// get the expected value of standing on this hand
		exp_stand(bet, htmp, dealer, shoe, &all_exp[STAND]);
	}

	// simulate the expected value of hitting 
	if(allowed[HIT]) { // should be always

		// hitting precludes anything but hit or stand afterwards
		memcpy(acttmp, allowed, 6*sizeof(int));
		acttmp[SPLIT] = 0; 
		acttmp[DOUBLE] = 0;
		acttmp[SURRENDER] = 0;
		acttmp[INSURANCE] = 0;

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
				expected_value(prb*bet, htmp, dealer, stmp, acttmp, &batmp, exptmp, depth+1);
				all_exp[HIT] += exptmp[batmp]; // use the action giving the highest expected outcome
			}
		}
	}

	// simulate the expected value of doubling (allowed exactly one more card) 
	if(allowed[DOUBLE]) { 
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
				exp_stand(2.0*prb*bet, htmp, dealer, stmp, exptmp);
				all_exp[DOUBLE] += exptmp[0];
			} 
		}
	}

	// simulate splitting, if hand is a pair and splitting is allowed
	allowed[SPLIT] *= hand.ispair;
	if(allowed[SPLIT]) {

		memcpy(acttmp, allowed, 6*sizeof(int));
		acttmp[SPLIT] -= 1; // most blackjack rules set the initial value of allowed[SPLIT] to 2
		acttmp[DOUBLE] = 1; // TODO: doubling usually not allowed after splitting
	
		// we must simulate all possible combinations of the next two cards
		// to precisely capture the state of the deck after two subsequent draws 
		all_exp[SPLIT] = 0.0;
		htmp = hand;
		htmp.points /= 2; htmp.softness /= 2;
		htmp.ispair = 0;
		for(c0 = 2; c0 <= 11; ++c0) {
			st0 = shoe;
			ht0 = htmp;
			prc0 = deal_card_to_hand_choose(&st0, &ht0, c0); 
			for(c1 = 2; c1 <= 11; ++c1) {
				st1 = st0;
				ht1 = htmp;
				prc1 = deal_card_to_hand_choose(&st1, &ht1, c1); 
				expected_value(prc0*prc1*bet, ht0, dealer, st0, acttmp, &batmp, exptmp, depth+1);
				all_exp[SPLIT] += exptmp[batmp];
				expected_value(prc0*prc1*bet, ht1, dealer, st1, acttmp, &batmp, exptmp, depth+1);
				all_exp[SPLIT] += exptmp[batmp];
			}
		}
	}

	// Decide which action yields the greatest expected value,
	// given the current knowledge of the deck and visible cards
	max_exp = -1000*bet;
	for(a = 0; a < 6; ++a) {
		if(!allowed[a]) continue;
		if(all_exp[a] > max_exp) {
			*best_action = a;
			max_exp = all_exp[a];
		}
	}


	// TODO: check player 21
	// TODO: check dealer 21, insurance, etc
	// Natural blackjack gets checked first
#if 0

	// if we are just post-deal and must check dealer BJ
	if(depth == 2) {

	
	}
#endif

}


// gives the expected winnings if the player stands
void exp_stand(real bet, Hand hand, Hand dealer, Shoe shoe, real* exp) {

	int c;
	real prb, exptmp;
	Hand dtmp;
	Shoe stmp;

	// stop if bet << 1
	*exp = 0.0;
	if(bet < ERRTOL) 
		return;

	// the dealer must hit
	// TODO: rule variants!
	if(dealer.points < 17) {

		// simulate the dealers hit/stand/bust, recursing as needed
		for(c = 2; c <= 11; ++c) {
			dtmp = dealer;
			stmp = shoe;
			if(stmp.num[c] <= 0) continue;
	
			// bust or recurse, weighting sub-expected values
			// by the probability that c is drawn
			prb = deal_card_to_hand_choose(&stmp, &dtmp, c); 
			if(dtmp.points > 21) {
				*exp += prb*bet;	
			} 
			else {
				exp_stand(prb*bet, hand, dtmp, stmp, &exptmp);
				*exp += exptmp;
			} 
		}
	}

	// the dealer must stand. See who won.
	else {
		if(dealer.points < hand.points) 
			*exp = +1.0*bet;
		if(dealer.points == hand.points)
			*exp = 0.0; 
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
		*my_ind = 36 - (hand.points/2); 
	else if(hand.softness)
		*my_ind = 37 - hand.points;
	else 
		*my_ind = 20 - hand.points;

	*dealer_ind = (dealer.points-2);
}


